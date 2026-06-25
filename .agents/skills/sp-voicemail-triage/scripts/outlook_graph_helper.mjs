#!/usr/bin/env node
import AuthManager, { resolveAuthScopes } from "../../../../.cursor/bin/ms365-mcp/node_modules/@softeria/ms-365-mcp-server/dist/auth.js";
import { createTokenCacheStorage } from "../../../../.cursor/bin/ms365-mcp/node_modules/@softeria/ms-365-mcp-server/dist/token-cache-storage.js";

const args = parseArgs(process.argv.slice(2));
const DEFAULT_VM_FOLDER_NAME = (process.env.VM_MAIL_FOLDER_NAME || "VM").trim() || "VM";

function parseArgs(argv) {
  const out = { command: "list-voicemails", messageId: "", attachmentId: "", to: "", comment: "", subject: "" };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (
      a === "list-voicemails" ||
      a === "scan-voicemails" ||
      a === "search-mail" ||
      a === "list-recent-inbox" ||
      a === "list-mail-folders" ||
      a === "get-message" ||
      a === "list-attachments" ||
      a === "download-attachment" ||
      a === "forward-message" ||
      a === "whoami"
    ) {
      out.command = a;
    } else if (a === "--message-id") out.messageId = argv[++i] || "";
    else if (a === "--attachment-id") out.attachmentId = argv[++i] || "";
    else if (a === "--to") out.to = argv[++i] || "";
    else if (a === "--comment") out.comment = argv[++i] || "";
    else if (a === "--subject") out.subject = argv[++i] || "";
  }
  return out;
}

async function getGraphToken(authManager) {
  return authManager.getToken();
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

function folderNameMatches(name, target) {
  return String(name || "").trim().toLowerCase() === target.trim().toLowerCase();
}

async function listChildFolders(token, parentFolderId) {
  const folders = [];
  let url = `/me/mailFolders/${encodeURIComponent(parentFolderId)}/childFolders?$select=id,displayName,totalItemCount,parentFolderId&$top=100`;
  while (url) {
    const page = await graphFetch(token, url);
    folders.push(...(page.value || []));
    url = page["@odata.nextLink"] || "";
  }
  return folders;
}

async function resolveVmFolder(token) {
  const overrideId = (process.env.VM_MAIL_FOLDER_ID || "").trim();
  if (overrideId) {
    const folder = await graphFetch(
      token,
      `/me/mailFolders/${encodeURIComponent(overrideId)}?$select=id,displayName,totalItemCount,parentFolderId`
    );
    return { folder, source: "env:VM_MAIL_FOLDER_ID" };
  }

  const inbox = await graphFetch(token, `/me/mailFolders/inbox?$select=id,displayName`);
  const childFolders = await listChildFolders(token, inbox.id);
  const childMatch = childFolders.find((folder) => folderNameMatches(folder.displayName, DEFAULT_VM_FOLDER_NAME));
  if (childMatch) {
    return { folder: childMatch, source: `inbox/child:${DEFAULT_VM_FOLDER_NAME}` };
  }

  let url = `/me/mailFolders?$select=id,displayName,totalItemCount,parentFolderId&$top=100`;
  while (url) {
    const page = await graphFetch(token, url);
    const match = (page.value || []).find((folder) => folderNameMatches(folder.displayName, DEFAULT_VM_FOLDER_NAME));
    if (match) {
      return { folder: match, source: `mailFolders:${DEFAULT_VM_FOLDER_NAME}` };
    }
    url = page["@odata.nextLink"] || "";
  }

  throw new Error(
    `Outlook VM folder "${DEFAULT_VM_FOLDER_NAME}" not found. Set VM_MAIL_FOLDER_ID or VM_MAIL_FOLDER_NAME.`
  );
}

async function listVoicemailMessages(token, { useSearch = false } = {}) {
  const days = Number(process.env.VM_LOOKBACK_DAYS || "7");
  const sinceMs = Date.now() - days * 24 * 60 * 60 * 1000;
  const { folder, source } = await resolveVmFolder(token);
  const select = "$select=id,subject,from,receivedDateTime,isRead,hasAttachments,bodyPreview,parentFolderId";
  const folderId = encodeURIComponent(folder.id);
  let url = useSearch
    ? `/me/mailFolders/${folderId}/messages?$search="subject:New voicemail"&${select}&$top=100`
    : `/me/mailFolders/${folderId}/messages?${select}&$top=100&$orderby=receivedDateTime desc`;
  const items = [];
  while (url) {
    const page = await graphFetch(
      token,
      url,
      useSearch ? { headers: { ConsistencyLevel: "eventual" } } : undefined
    );
    let stop = false;
    for (const msg of page.value || []) {
      const subject = String(msg.subject || "");
      const receivedMs = Date.parse(String(msg.receivedDateTime || ""));
      if (!useSearch && Number.isFinite(receivedMs) && receivedMs < sinceMs) {
        stop = true;
        continue;
      }
      if (
        /new voicemail/i.test(subject) &&
        !subject.trim().toUpperCase().startsWith("FW:") &&
        msg.hasAttachments === true &&
        Number.isFinite(receivedMs) &&
        receivedMs >= sinceMs
      ) {
        items.push(msg);
      }
    }
    if (stop) break;
    url = page["@odata.nextLink"] || "";
  }
  items.sort((a, b) => Date.parse(b.receivedDateTime) - Date.parse(a.receivedDateTime));
  return {
    value: items,
    count: items.length,
    lookbackDays: days,
    folder: {
      id: folder.id,
      displayName: folder.displayName,
      totalItemCount: folder.totalItemCount,
      source,
    },
  };
}

async function main() {
  const storage = await createTokenCacheStorage({ allowCommandStorage: false, logProvider: false });
  const authManager = await AuthManager.create(resolveAuthScopes({ orgMode: true }), {}, { storage });
  await authManager.loadTokenCache();
  const token = await getGraphToken(authManager);

  if (args.command === "search-mail") {
    const query = process.env.VM_SEARCH || "New voicemail";
    const select = "$select=id,subject,from,receivedDateTime,isRead,hasAttachments,bodyPreview,parentFolderId";
    const search = `$search="${query}"`;
    const url = `/me/messages?${search}&${select}&$top=50`;
    const data = await graphFetch(token, url, { headers: { ConsistencyLevel: "eventual" } });
    process.stdout.write(JSON.stringify(data, null, 2));
    return;
  }

  if (args.command === "scan-voicemails" || args.command === "list-voicemails") {
    const data = await listVoicemailMessages(token, { useSearch: args.command === "list-voicemails" });
    process.stdout.write(JSON.stringify(data, null, 2));
    return;
  }

  if (args.command === "list-mail-folders") {
    const inbox = await graphFetch(token, `/me/mailFolders/inbox?$select=id,displayName,totalItemCount`);
    const childFolders = await listChildFolders(token, inbox.id);
    const vmFolder = await resolveVmFolder(token);
    process.stdout.write(JSON.stringify({ inbox, childFolders, vmFolder }, null, 2));
    return;
  }

  if (args.command === "whoami") {
    const me = await graphFetch(token, `/me?$select=displayName,userPrincipalName,mail`);
    const folders = await graphFetch(token, `/me/mailFolders/inbox?$select=displayName,totalItemCount,unreadItemCount`);
    const vmFolder = await resolveVmFolder(token);
    process.stdout.write(JSON.stringify({ me, inbox: folders, vmFolder }, null, 2));
    return;
  }

  if (args.command === "list-recent-inbox") {
    const select = "$select=id,subject,from,receivedDateTime,isRead,hasAttachments,bodyPreview";
    const url = `/me/mailFolders/inbox/messages?${select}&$top=25&$orderby=receivedDateTime desc`;
    const data = await graphFetch(token, url);
    process.stdout.write(JSON.stringify(data, null, 2));
    return;
  }

  if (args.command === "get-message") {
    const data = await graphFetch(
      token,
      `/me/messages/${encodeURIComponent(args.messageId)}?$select=id,subject,from,receivedDateTime,body,hasAttachments`
    );
    process.stdout.write(JSON.stringify(data, null, 2));
    return;
  }

  if (args.command === "list-attachments") {
    const data = await graphFetch(
      token,
      `/me/messages/${encodeURIComponent(args.messageId)}/attachments?$select=id,name,contentType,size`
    );
    process.stdout.write(JSON.stringify(data, null, 2));
    return;
  }

  if (args.command === "download-attachment") {
    const data = await graphFetch(
      token,
      `/me/messages/${encodeURIComponent(args.messageId)}/attachments/${encodeURIComponent(args.attachmentId)}`
    );
    if (!data.contentBytes) {
      throw new Error("Attachment has no inline contentBytes");
    }
    process.stdout.write(Buffer.from(data.contentBytes, "base64"));
    return;
  }

  if (args.command === "forward-message") {
    const payload = {
      comment: args.comment,
      toRecipients: [{ emailAddress: { address: args.to } }],
    };
    if (args.subject) {
      payload.message = { subject: args.subject };
    }
    await graphFetch(token, `/me/messages/${encodeURIComponent(args.messageId)}/forward`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    process.stdout.write(JSON.stringify({ ok: true, to: args.to, messageId: args.messageId }));
    return;
  }

  throw new Error(`Unknown command: ${args.command}`);
}

main().catch((err) => {
  console.error(JSON.stringify({ ok: false, error: String(err.message || err) }));
  process.exit(1);
});
