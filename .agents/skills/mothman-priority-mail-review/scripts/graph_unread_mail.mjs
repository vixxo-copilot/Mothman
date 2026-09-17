#!/usr/bin/env node
/**
 * Pull unread Outlook messages for Crystal's priority mail boxes.
 * Auth: same MS365 MCP token cache as sf-case-email-sync.
 */
import AuthManager, { resolveAuthScopes } from "../../../../.cursor/bin/ms365-mcp/node_modules/@softeria/ms-365-mcp-server/dist/auth.js";
import { createTokenCacheStorage } from "../../../../.cursor/bin/ms365-mcp/node_modules/@softeria/ms-365-mcp-server/dist/token-cache-storage.js";

const SELECT_FOLDER =
  "id,displayName,unreadItemCount,totalItemCount,childFolderCount,parentFolderId";
const SELECT_MSG =
  "id,subject,from,receivedDateTime,bodyPreview,isRead,hasAttachments,importance,conversationId,flag,webLink";

function parseArgs(argv) {
  const out = { extra: [], maxPerFolder: 120 };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === "--extra-folder") out.extra.push(argv[++i] || "");
    else if (a === "--max") out.maxPerFolder = Number(argv[++i] || "120");
  }
  return out;
}

async function graphFetch(token, path, init = {}) {
  const url = path.startsWith("http") ? path : `https://graph.microsoft.com/v1.0${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
      ...(init.headers || {}),
    },
  });
  const text = await res.text();
  let body;
  try {
    body = text ? JSON.parse(text) : {};
  } catch {
    body = { raw: text };
  }
  if (!res.ok) {
    throw new Error(`Graph ${res.status}: ${JSON.stringify(body)}`);
  }
  return body;
}

async function getToken() {
  const storage = await createTokenCacheStorage({
    allowCommandStorage: false,
    logProvider: false,
  });
  const authManager = await AuthManager.create(
    resolveAuthScopes({ orgMode: true }),
    {},
    { storage }
  );
  await authManager.loadTokenCache();
  return authManager.getToken();
}

async function paged(token, firstUrl) {
  const items = [];
  let url = firstUrl;
  while (url) {
    const data = await graphFetch(token, url);
    items.push(...(data.value || []));
    const next = data["@odata.nextLink"];
    url = next ? next.replace("https://graph.microsoft.com/v1.0", "") : null;
  }
  return items;
}

async function listChildren(token, folderId) {
  return paged(
    token,
    `/me/mailFolders/${encodeURIComponent(folderId)}/childFolders?$select=${SELECT_FOLDER}&$top=50`
  );
}

async function walk(token, folderId, pathParts) {
  const kids = await listChildren(token, folderId);
  const out = [];
  for (const k of kids) {
    const path = [...pathParts, k.displayName];
    out.push({ ...k, path: path.join(" / ") });
    if ((k.childFolderCount || 0) > 0) {
      out.push(...(await walk(token, k.id, path)));
    }
  }
  return out;
}

function norm(s) {
  return String(s || "").toLowerCase();
}

function matchAll(name, needles) {
  const n = norm(name);
  return needles.every((x) => n.includes(x));
}

function findFolder(folders, extraNames, spec) {
  if (spec.wellKnown === "inbox") {
    return folders.find((f) => f._wellKnown === "inbox") || null;
  }
  const extras = extraNames.map(norm).filter(Boolean);
  const hit = folders.find((f) => {
    const n = norm(f.displayName);
    if (extras.includes(n)) return true;
    if (spec.name_all && matchAll(f.displayName, spec.name_all)) return true;
    if (spec.name_any && spec.name_any.some((x) => n.includes(x))) return true;
    return false;
  });
  return hit || null;
}

async function unreadInFolder(token, folderId, max) {
  const filter = encodeURIComponent("isRead eq false");
  const select = encodeURIComponent(SELECT_MSG);
  const order = encodeURIComponent("receivedDateTime asc");
  let url =
    `/me/mailFolders/${encodeURIComponent(folderId)}/messages` +
    `?$filter=${filter}&$orderby=${order}&$select=${select}&$top=50`;
  const items = [];
  while (url && items.length < max) {
    let data;
    try {
      data = await graphFetch(token, url);
    } catch (err) {
      if (String(err.message || err).includes("$orderby")) {
        url =
          `/me/mailFolders/${encodeURIComponent(folderId)}/messages` +
          `?$filter=${filter}&$select=${select}&$top=50`;
        data = await graphFetch(token, url);
      } else {
        throw err;
      }
    }
    items.push(...(data.value || []));
    const next = data["@odata.nextLink"];
    url = next && items.length < max ? next.replace("https://graph.microsoft.com/v1.0", "") : null;
  }
  items.sort((a, b) => String(a.receivedDateTime).localeCompare(String(b.receivedDateTime)));
  return items.slice(0, max);
}

const BOX_SPECS = [
  {
    id: "inbox",
    label: "Inbox",
    wellKnown: "inbox",
  },
  {
    id: "maria_leslie_spm",
    label: "Maria/Leslie/SPM & Adam",
    name_all: ["maria", "leslie"],
  },
  {
    id: "kate_ormb",
    label: "ORMB/Kate",
    name_any: ["ormb"],
  },
  {
    id: "invoices_statements",
    label: "Invoices/Statements",
    name_all: ["invoice", "statement"],
  },
];

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const token = await getToken();

  const inbox = await graphFetch(
    token,
    `/me/mailFolders/inbox?$select=${SELECT_FOLDER}`
  );
  inbox._wellKnown = "inbox";
  inbox.path = "Inbox";

  const underInbox = await walk(token, inbox.id, ["Inbox"]);
  const folders = [inbox, ...underInbox];

  const boxes = [];
  for (const spec of BOX_SPECS) {
    const folder = findFolder(folders, args.extra, spec);
    if (!folder) {
      boxes.push({
        id: spec.id,
        label: spec.label,
        found: false,
        unread_folder_count: 0,
        messages: [],
        error: "Folder not found",
      });
      continue;
    }
    const messages = await unreadInFolder(token, folder.id, args.maxPerFolder);
    boxes.push({
      id: spec.id,
      label: spec.label,
      found: true,
      folder_id: folder.id,
      folder_name: folder.displayName,
      folder_path: folder.path || folder.displayName,
      unread_folder_count: folder.unreadItemCount || messages.length,
      total_item_count: folder.totalItemCount || 0,
      messages,
    });
  }

  process.stdout.write(
    JSON.stringify(
      {
        ok: true,
        generated_at: new Date().toISOString(),
        boxes,
        folder_index: folders.map((f) => ({
          name: f.displayName,
          path: f.path,
          unread: f.unreadItemCount,
        })),
      },
      null,
      2
    )
  );
}

main().catch((err) => {
  console.error(JSON.stringify({ ok: false, error: String(err.message || err) }));
  process.exit(1);
});
