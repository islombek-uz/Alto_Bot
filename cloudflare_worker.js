function unauthorized() {
  return new Response("Unauthorized", { status: 401 });
}

function notFound() {
  return new Response("Not found", { status: 404 });
}

export default {
  async fetch(request, env) {
    if (
      !env.WORKER_API_SECRET ||
      !env.TELEGRAM_WEBHOOK_PATH ||
      !env.TELEGRAM_WEBHOOK_SECRET ||
      !env.PA_WEBHOOK_URL ||
      !env.PA_WEBHOOK_SECRET
    ) {
      return new Response("Worker configuration is incomplete", {
        status: 500,
      });
    }

    const url = new URL(request.url);
    const apiPrefix = `/api/${env.WORKER_API_SECRET}/`;
    const openRouterPrefix = `/openrouter/${env.WORKER_API_SECRET}/`;

    if (url.pathname.startsWith(apiPrefix)) {
      const apiPath = url.pathname.slice(apiPrefix.length - 1);
      const validTelegramPath =
        /^\/bot\d+:[A-Za-z0-9_-]+\/[A-Za-z0-9_]+$/.test(apiPath) ||
        /^\/file\/bot\d+:[A-Za-z0-9_-]+\/.+$/.test(apiPath);

      if (!validTelegramPath) {
        return notFound();
      }

      const target = new URL(`https://api.telegram.org${apiPath}`);
      target.search = url.search;
      return fetch(new Request(target, request));
    }

    if (url.pathname.startsWith(openRouterPrefix)) {
      const apiPath = url.pathname.slice(openRouterPrefix.length - 1);
      if (!apiPath.startsWith("/api/v1/")) {
        return notFound();
      }

      const target = new URL(`https://openrouter.ai${apiPath}`);
      target.search = url.search;
      return fetch(new Request(target, request));
    }

    const webhookPath = `/telegram-webhook/${env.TELEGRAM_WEBHOOK_PATH}`;
    if (url.pathname !== webhookPath || request.method !== "POST") {
      return notFound();
    }

    if (
      request.headers.get("X-Telegram-Bot-Api-Secret-Token") !==
      env.TELEGRAM_WEBHOOK_SECRET
    ) {
      return unauthorized();
    }

    return fetch(env.PA_WEBHOOK_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Worker-Auth": env.PA_WEBHOOK_SECRET,
      },
      body: request.body,
      redirect: "manual",
    });
  },
};
