import { chromium, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const base=process.env.LEADREVIVE_URL||'http://127.0.0.1:8000';
const browser=await chromium.launch();
try {
  const page=await browser.newPage({viewport:{width:1366,height:1000}});
  await page.goto(base);
  await page.getByRole('button',{name:'Recovery queue',exact:true}).click();
  await expect(page.locator('tbody tr')).toHaveCount(12);
  const change=async(label,value)=>{
    await Promise.all([page.waitForResponse(r=>r.url().includes('/api/leads?')&&r.status()===200),
      page.getByLabel(label,{exact:true}).selectOption(value)]);
    await expect(page.locator('tbody tr').first()).toBeVisible();
  };
  await change('Filter by follow-up','overdue');
  await change('Filter by owner','REP-1');
  let result=await (await page.request.get(base+'/api/leads?followup=overdue&owner=REP-1')).json();
  expect(result.items.every(r=>r.overdue&&r.owner_id==='REP-1')).toBe(true);
  await change('Sort leads','value');
  const byValue=await(await page.request.get(base+'/api/leads?followup=overdue&owner=REP-1&sort=value&page_size=12')).json();
  expect(byValue.items.every((r,i,a)=>i===0||r.estimated_value_paise<=a[i-1].estimated_value_paise)).toBe(true);
  await expect(page.locator('tbody tr').first()).toContainText(byValue.items[0].company);
  await change('Sort leads','priority');
  result=await(await page.request.get(base+'/api/leads?followup=overdue&owner=REP-1&sort=priority&page_size=12')).json();
  await expect(page.locator('tbody tr').first()).toContainText(result.items[0].company);
  expect(result.items.every((r,i,a)=>r.priority.score>0&&(i===0||r.priority.score<=a[i-1].priority.score))).toBe(true);
  await expect(page.locator('tbody tr')).toHaveCount(result.items.length);
  await expect(page.getByRole('heading',{name:'Loading your workspace'})).toHaveCount(0);
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:path.resolve('../screenshots/SS02b_Recovery_Queue_Loaded.png'),fullPage:true});
  await page.getByRole('button',{name:`Open ${result.items[0].lead_id}`,exact:true}).click();
  await expect(page.getByRole('heading',{name:result.items[0].company,exact:true})).toBeVisible();
  await expect(page.getByLabel('Assigned owner',{exact:true})).toHaveValue('REP-1');
  fs.writeFileSync(path.resolve('../data/processed/phase3_queue_verification.json'),JSON.stringify({
    result:'passed',visible_rows:result.items.length,filtered_total:result.total,filters:{owner:'REP-1',followup:'overdue'},
    checks:['fully loaded SQL records','owner + overdue filters','value descending','priority descending','open lead detail'],
    opened_lead_id:result.items[0].lead_id,screenshot:'SS02b_Recovery_Queue_Loaded.png'
  },null,2));
  console.log(`PASS: ${result.items.length} visible records, ${result.total} matches; filters/sorts/open verified.`);
} finally {await browser.close();}
