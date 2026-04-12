(function (window, document) {
  'use strict';

  // Защита от повторной инициализации, если файл случайно подключат дважды.
  if (window.__cadpointFooterCountersLoaded) {
    return;
  }
  window.__cadpointFooterCountersLoaded = true;

  function appendScript(src, id) {
    // Не создаём дубликаты, если скрипт уже есть в DOM.
    if (id && document.getElementById(id)) {
      return null;
    }
    var script = document.createElement('script');
    script.async = true;
    script.src = src;
    if (id) {
      script.id = id;
    }
    (document.head || document.body).appendChild(script);
    return script;
  }
  function initGoogleAnalytics() {
    // Поддерживаем старый UA-код, чтобы не ломать текущую статистику.
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function gtag() {
      window.dataLayer.push(arguments);
    };
    window.gtag('js', new Date());
    window.gtag('config', 'UA-9116991-1');
    appendScript('https://www.googletagmanager.com/gtag/js?id=UA-9116991-1', 'cadpoint-gtag-js');
  }

  function initYandexMetrika() {
    // Повторяем стандартный паттерн Metrika: сначала очередь вызовов, потом загрузка внешнего файла.
    window.ym = window.ym || function ym() {
      (window.ym.a = window.ym.a || []).push(arguments);
    };
    window.ym.l = 1 * new Date();
    window.ym(198477, 'init', {
      clickmap: true,
      trackLinks: true,
      accurateTrackBounce: true,
      webvisor: true,
    });
    appendScript('https://mc.yandex.ru/metrika/tag.js', 'cadpoint-yandex-metrika-js');
  }

  function initMailRuCounter() {
    // Rating Mail.ru тоже любит сначала получить очередь событий, а затем уже внешний код.
    window._tmr = window._tmr || [];
    window._tmr.push({
      id: '1612438',
      type: 'pageView',
      start: (new Date()).getTime(),
    });
    appendScript('https://top-fwz1.mail.ru/js/code.js', 'topmailru-code');
  }

  // Вызываем функции-счетчики
  initGoogleAnalytics();
  initYandexMetrika();
  initMailRuCounter();

})(window, document);

