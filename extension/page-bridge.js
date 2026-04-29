window.addEventListener("message", (event) => {
  if (event.source !== window || event.origin !== window.location.origin) {
    return;
  }

  const data = event.data;
  if (!data || data.source !== "offerscope-page" || data.type !== "OFFERSCOPE_AUTOFILL_REQUEST") {
    return;
  }

  chrome.runtime.sendMessage(
    {
      type: "OFFERSCOPE_AUTOFILL_REQUEST",
      payload: data.payload
    },
    (response) => {
      const runtimeError = chrome.runtime.lastError;
      if (runtimeError) {
        window.postMessage(
          {
            source: "offerscope-extension",
            type: "OFFERSCOPE_AUTOFILL_RESULT",
            requestId: data.requestId,
            ok: false,
            error: runtimeError.message
          },
          window.location.origin
        );
        return;
      }

      window.postMessage(
        {
          source: "offerscope-extension",
          type: "OFFERSCOPE_AUTOFILL_RESULT",
          requestId: data.requestId,
          ok: !!response?.ok,
          payload: response?.payload,
          error: response?.error
        },
        window.location.origin
      );
    }
  );
});
