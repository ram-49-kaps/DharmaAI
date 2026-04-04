const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:3000');
  
  const icon = await page.evaluate(() => {
    const el = document.querySelector('.logo-icon svg');
    if (!el) return 'No SVG found';
    return {
      outerHTML: el.outerHTML,
      width: el.getBoundingClientRect().width,
      height: el.getBoundingClientRect().height,
      clientWidth: el.clientWidth,
      clientHeight: el.clientHeight,
      viewBox: el.getAttribute('viewBox'),
      attrs: Array.from(el.attributes).map(a => `${a.name}="${a.value}"`).join(' ')
    };
  });
  
  console.log(JSON.stringify(icon, null, 2));
  await browser.close();
})();
