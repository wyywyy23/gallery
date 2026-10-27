var themeToggle = document.getElementById('theme-toggle');

if (themeToggle) {
  themeToggle.addEventListener('click', function () {
    var isLight = document.documentElement.getAttribute('data-theme') !== 'light';
    document.documentElement.setAttribute('data-theme', isLight ? 'light' : 'dark');
    var label = isLight ? 'Switch to dark mode' : 'Switch to light mode';
    themeToggle.setAttribute('aria-label', label);
    themeToggle.setAttribute('title', label);
    themeToggle.setAttribute('aria-pressed', String(isLight));
  });
}

var id = 'gallery';

function reqListener() {
  var renderer
  switch (layoutStyle) {
    case COLUMNS:
      renderer = new VerticalRenderer(id);
      break;
    case ROWS:
      renderer = new HorizontalRenderer(id);
      break;
    case SQUARES:
      renderer = new SquareRenderer(id);
      break;
  }
  var config = new Config(JSON.parse(this.responseText), configuration);
  renderer.render(config);
  lazyload();
}


window.onload = function() {
  var oReq = new XMLHttpRequest();
  oReq.addEventListener("load", reqListener);
  oReq.open("GET", "config.json");
  oReq.send();

  let igElem = document.getElementById('instagram');
  let footerElem = document.querySelector('div.footer');
  if (igElem && footerElem && igElem.href === 'https://www.instagram.com/') {
    footerElem.remove();
  }
};
