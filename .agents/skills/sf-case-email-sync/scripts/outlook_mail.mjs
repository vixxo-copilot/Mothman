#!/usr/bin/env node
/**
 * Graph mail helpers for sf-case-email-sync.
 * Commands: search, get-message, list-attachments, download-attachment, download-mime, whoami
 */
import AuthManager, { resolveAuthScopes } from "../../../../.cursor/bin/ms365-mcp/node_modules/@softeria/ms-365-mcp-server/dist/auth.js";
import { createTokenCacheStorage } from "../../../../.cursor/bin/ms365-mcp/node_modules/@softeria/ms-365-mcp-server/dist/token-cache-storage.js";

const args = parseArgs(process.argv.slice(2));

function parseArgs(argv) {
  const out = { command: "whoami", query: "", messageId: "", attachmentId: "", top: 50 };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (
      a === "search" ||
      a === "get-message" ||
      a === "list-attachments" ||
      a === "download-attachment" ||
      a === "download-mime" ||
      a === "whoami"
    ) {
      out.command = a;
    } else if (a === "--query") out.query = argv[++i] || "";
    else if (a === "--message-id") out.messageId = argv[++i] || "";
    else if (a === "--attachment-id") out.attachmentId = argv[++i] || "";
    else if (a === "--top") out.top = Number(argv[++i] || "50");
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
  const storage = await createTokenCacheStorage({ allowCommandStorage: false, logProvider: false });
  const authManager = await AuthManager.create(resolveAuthScopes({ orgMode: true }), {}, { storage });
  await authManager.loadTokenCache();
  return authManager.getToken();
}

async function searchMessages(token, query, top) {
  const select =
    "$select=id,subject,from,toRecipients,receivedDateTime,sentDateTime,hasAttachments,bodyPreview,internetMessageId";
  const search = `$search="${query.replace(/"/g, '\\"')}"`;
  const url = `/me/messages?${search}&${select}&$top=${top}`;
  const data = await graphFetch(token, url, { headers: { ConsistencyLevel: "eventual" } });
  return data.value || [];
}

async function main() {
  const token = await getToken();

  if (args.command === "whoami") {
    const me = await graphFetch(token, `/me?$select=displayName,userPrincipalName,mail`);
    process.stdout.write(JSON.stringify(me, null, 2));
    return;
  }

  if (args.command === "search") {
    const query = args.query || process.env.SF_CASE_SYNC_SEARCH || "";
    if (!query) throw new Error("search requires --query or SF_CASE_SYNC_SEARCH");
    const items = await searchMessages(token, query, args.top);
    process.stdout.write(JSON.stringify({ value: items, count: items.length, query }, null, 2));
    return;
  }

  if (args.command === "get-message") {
    const select =
      "id,subject,from,toRecipients,ccRecipients,receivedDateTime,sentDateTime,body,internetMessageId,hasAttachments";
    const data = await graphFetch(
      token,
      `/me/messages/${encodeURIComponent(args.messageId)}?$select=${select}`
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
    if (!data.contentBytes) throw new Error("Attachment has no inline contentBytes");
    process.stdout.write(Buffer.from(data.contentBytes, "base64"));
    return;
  }

  if (args.command === "download-mime") {
    const url = `/me/messages/${encodeURIComponent(args.messageId)}/$value`;
    const res = await fetch(`https://graph.microsoft.com/v1.0${url}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`MIME fetch failed ${res.status}`);
    process.stdout.write(Buffer.from(await res.arrayBuffer()));
    return;
  }

  throw new Error(`Unknown command: ${args.command}`);
}

main().catch((err) => {
  console.error(JSON.stringify({ ok: false, error: String(err.message || err) }));
  process.exit(1);
});
