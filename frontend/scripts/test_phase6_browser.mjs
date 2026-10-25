import {chromium,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
const browser=await chromium.launch();const context=await browser.newContext({viewport:{width:1440,height:1000}});const page=await context.newPage();
const errors=[];page.on('pageerror',e=>errors.push(e.message));const checks=[];
try {
  await page.goto('http://127.0.0.1:18000');
  await expect(page.getByRole('heading',{name:'A clearer view. A stronger follow-up.'})).toBeVisible();
  await page.getByRole('button',{name:'Recovery queue',exact:true}).click();
  await expect(page.locator('tbody tr').first()).toBeVisible();
  checks.push('Clean Docker UI loads Overview and populated Recovery Queue');
  await page.screenshot({path:'../screenshots/SS13_Clean_Install_Queue.png',fullPage:true});
  await page.getByRole('button',{name:'Reports',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Reports & management briefing'})).toBeVisible();
  const response=page.waitForResponse(r=>r.url().endsWith('/api/reports/generate')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Generate report pack',exact:true}).click();
  expect((await response).status()).toBe(200);
  await expect(page.getByRole('heading',{name:'Report pack ready'})).toBeVisible();
  const download=page.waitForEvent('download');await page.getByRole('link',{name:'LeadRevive_Report_SYNTHETIC.pdf',exact:true}).first().click();
  expect(await (await download).failure()).toBeNull();
  checks.push('Clean Docker Reports UI generates and downloads an actual PDF');
  const axe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa']).analyze();expect(axe.violations).toEqual([]);
  checks.push('Reports controls pass automated WCAG A/AA checks');
  await page.screenshot({path:'../screenshots/SS14_Clean_Install_Reports.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();expect(errors).toEqual([]);
  checks.push('Mobile Reports layout fits viewport; no JavaScript errors');
  fs.writeFileSync('../data/processed/phase6_browser.json',JSON.stringify({result:'passed',checks},null,2));console.log(JSON.stringify({result:'passed',checks},null,2));
} finally {await browser.close();}
