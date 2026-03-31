// GOOGLE ANALYTICS LOADER

(function () {

  const GA_ID = "G-XXXXXXXXXX"; // <-- PUT YOUR REAL ID HERE

  // Load script
  const script = document.createElement("script");
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
  document.head.appendChild(script);

  // Setup dataLayer
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  window.gtag = gtag;

  gtag('js', new Date());
  gtag('config', GA_ID, {
    page_path: window.location.pathname
  });

})();
