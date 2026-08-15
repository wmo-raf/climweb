const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const outPath = path.resolve(
    __dirname,
    '../docs/_static/images/settings/style_guide.png'
  );

  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  console.log('Navigating to /style-guide/...');
  await page.goto('http://localhost/style-guide/', { waitUntil: 'networkidle2', timeout: 30000 });

  const title = await page.title();
  console.log('Page title:', title);

  // Scroll to trigger lazy-loaded sections, then screenshot the top portion
  await page.evaluate(() => window.scrollTo(0, 0));

  await page.screenshot({ path: outPath, fullPage: false });
  console.log('Saved:', outPath);

  await browser.close();
})();
