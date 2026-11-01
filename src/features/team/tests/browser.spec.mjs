// Optional browser regression check; supply Playwright from your test environment.
const { chromium } = await import(process.env.MULA_PLAYWRIGHT_MODULE || "playwright");
const baseURL = process.env.MULA_TEST_URL || "http://127.0.0.1:3001";
import assert from 'node:assert/strict';
const browser=await chromium.launch({headless:true,executablePath:process.env.MULA_BROWSER_PATH});
try {
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 let signedIn=true;
 await page.route('**/api/auth/me',route=>{if(signedIn)return route.fulfill({json:{username:'Rafa'}});return route.fulfill({status:401,json:{detail:'Please sign in.'}});});
 await page.route('**/api/conversation',route=>route.fulfill({json:{session_id:'12345678-1234-1234-1234-123456789012',messages:[]}}));
 await page.route('**/api/auth/logout',route=>{signedIn=false;return route.fulfill({json:{status:'ok'}});});
 await page.goto(baseURL + "/");
 const core=page.locator('canvas.operator-core');await core.waitFor();
 const frame1=await core.evaluate(e=>e.toDataURL());
 await page.waitForTimeout(650);
 const frame2=await core.evaluate(e=>e.toDataURL());assert.notEqual(frame1,frame2,'idle motion must advance without audio');
 await page.emulateMedia({reducedMotion:'reduce'});await page.waitForTimeout(200);
 const still1=await core.evaluate(e=>e.toDataURL());await page.waitForTimeout(350);
 const still2=await core.evaluate(e=>e.toDataURL());assert.equal(still1,still2,'reduced motion must stay still');
 await page.getByRole('link',{name:'My team',exact:true}).filter({visible:true}).click();
 await page.getByRole('heading',{name:'Your ambition. A little more support.'}).waitFor();
 assert.match(page.url(),/\/team$/);
 assert.equal(await page.locator('.agent-station').count(),6);
 assert.equal(await page.locator('.agent-station.available').count(),1);
 await page.screenshot({path:'/tmp/mula-team-desktop.png',fullPage:true});
 await page.getByRole('button',{name:'Explore Procurement',exact:true}).click();
 await page.getByRole('heading',{name:'Procurement',exact:true}).waitFor();
 assert.equal(await page.getByText('This agent isn’t available to hire yet.').isVisible(),true);
 assert.equal(await page.getByRole('link',{name:'Talk to Operator'}).count(),0);
 await page.getByRole('button',{name:'Explore Operator',exact:true}).focus();await page.keyboard.press('Enter');
 await page.getByRole('link',{name:'Talk to Operator'}).waitFor();
 await page.reload();await page.getByRole('heading',{name:'Your ambition. A little more support.'}).waitFor();
 for(const width of [1024,768,390]) {
   await page.setViewportSize({width,height:900});
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'no horizontal overflow at '+width);
 }
 await page.getByRole('button',{name:'Explore Inventory',exact:true}).click();
 await page.screenshot({path:'/tmp/mula-team-mobile.png',fullPage:true});
 await page.getByRole('link',{name:'Back to Operator'}).click();await core.waitFor();
 await page.getByRole('link',{name:'My team',exact:true}).filter({visible:true}).click();
 await page.getByRole('button',{name:'Sign out',exact:true}).filter({visible:true}).click();
 await page.getByRole('heading',{name:'Welcome back',exact:true}).waitFor();
 await page.goto(baseURL + "/team");
 await page.getByRole('heading',{name:'Welcome back',exact:true}).waitFor();
 assert.equal(await page.locator('.office').count(),0);
 assert.deepEqual(errors,[]);
 console.log('PASS: idle animation, reduced motion, navigation, six roles, honest availability, selection, keyboard, refresh, responsive layouts, logout and signed-out protection.');
} finally {await browser.close();}
