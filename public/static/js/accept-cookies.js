(function (window, document) {
  'use strict';

  // Защита от повторного подключения, если файл случайно вставят дважды.
  if (window.__cadpointAcceptCookiesLoaded) {
    return;
  }
  window.__cadpointAcceptCookiesLoaded = true;

  var COOKIE_NAME = 'cookie_accept';
  var COOKIE_VALUE = 'yes';
  var COOKIE_TTL_MS = 7_948_800_000;
  var bannerId = 'cookies_accept';
  var buttonId = 'cookies_accept_button';

  function acceptCookies() {
    // Сохраняем согласие тем же ключом, что и раньше, чтобы серверная логика не менялась.
    var cookieAcceptDate = new Date();
    cookieAcceptDate.setTime(cookieAcceptDate.getTime() + COOKIE_TTL_MS);
    document.cookie = COOKIE_NAME + '=' + COOKIE_VALUE + ';expires=' + cookieAcceptDate;

    var banner = document.getElementById(bannerId);
    if (banner) {
      banner.remove();
    }
  }

  function bindAcceptButton() {
    var button = document.getElementById(buttonId);
    if (!button) {
      return;
    }

    button.addEventListener('click', acceptCookies);
  }

  bindAcceptButton();
})(window, document);

