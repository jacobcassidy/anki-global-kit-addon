if (typeof hasMyCustomScript === 'undefined' && !globalThis.ankiGlobalKitScriptLoading) {
  globalThis.ankiGlobalKitScriptLoading = new Promise((resolve, reject) => {
    const script = document.createElement('script');

    script.src = '_anki-global-kit.min.js';
    script.async = true;
    script.onload = resolve;
    script.onerror = () => {
      script.remove();
      reject(new Error('Unable to load Anki Global Kit card script.'));
    };

    document.head.appendChild(script);
  }).catch((error) => {
    globalThis.ankiGlobalKitScriptLoading = null;
    console.warn(error);
  });
}
