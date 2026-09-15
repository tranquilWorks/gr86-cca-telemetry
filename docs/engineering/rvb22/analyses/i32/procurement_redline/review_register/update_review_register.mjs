import fs from 'node:fs/promises';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../../..');
const path=root+'/current/GR86_CCA_RevB_ERB_CCB_Review_Register.xlsx';
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(path));
if(process.argv.includes('--edit')) {
  const dir=root+'/analyses/i32/procurement_redline';
  const result=JSON.parse(await fs.readFile(dir+'/FINAL_REDLINE_VERIFICATION.json','utf8'));
  const old={}; const edits=[];
  for(let i=0;i<19;i++) {
    const s=wb.worksheets.getItemAt(i),r=s.getUsedRange();
    old[s.name]={values:r.values,formulas:r.formulas,address:r.address};
  }
  function set(sheet,cell,value) {const s=wb.worksheets.getItem(sheet); edits.push({sheet,cell,before:s.getRange(cell).values[0][0],after:value});s.getRange(cell).values=[[value]];}
  set('Start Here','A1','GR86 CCA I32 procurement redline');
  set('Start Here','A3','Current authority: analyses/i32/procurement_redline/FINAL_REDLINE_VERIFICATION.json and README.md. Earlier source-specific review records are historical.');
  set('Start Here','A4','Desktop redline verified. Supplier process acceptance and physical qualification remain open.');
  set('Start Here','C6','HISTORICAL CLOSED');set('Start Here','E6','HISTORICAL OPEN');
  set('Start Here','A9','HISTORICAL CRITERION CLOSURES');
  set('Start Here','A11','I32: 13 frozen substitutions, qualified package changes, 177 fitted parts, 175 factory CPL rows. F101 and U401 remain local/manual installation.');
  set('Start Here','A13','Fresh ngspice 42: 32/32 completed, 17/17 normal sequences. Reset margin +11.81634 mV; upper-rail margin +23.39023 mV.');
  set('Start Here','A15','Firmware: 32 source files unchanged. Retain the verified 160 MHz recovery build and its 28/28 release checks. No hardware was flashed.');
  set('Start Here','A19','Factory BOM/CPL and fabrication outputs regenerated. Nine exact frozen MPN/C-number purchase paths verified; L121 supplier process approval remains open.');
  set('Start Here','A21','The original 290-criterion ledger and its wording are retained. Historical counts are not a new product-level qualification or a re-adjudication of every criterion.');
  set('Start Here','A23','Current native source: candidate/cad/. Source/hash authority: current/SOURCE_EFFECTIVITY.json. ERC, DRC, unconnected and parity findings are zero.');
  set('Start Here','A27','Remaining: supplier DFM/assembly acceptance, first-article fit and thermal correlation, electrical/EMC tests, installed vehicle validation and unit acceptance.');
  set('RVB22 Current','A1','GR86 CCA I32 procurement redline');
  set('RVB22 Current','A2','Original criterion ledger retained. Counts below are historical; the current redline evidence is in analyses/i32/procurement_redline/.');
  set('RVB22 Current','C4','HISTORICAL CLOSED');set('RVB22 Current','E4','HISTORICAL OPEN');
  set('RVB22 Current','A8','Native, procurement, manufacturing and package screens pass. Supplier and physical validation remain open.');
  set('RVB22 Current','A11','Historical change since user baseline');
  set('RVB22 Current','D15','Historical 290-criterion dispositions. Current redline: procurement_redline/README.md.');
  set('RVB22 Current','D16','Earlier findings retained. New package, route and sourcing evidence: procurement_redline/.');
  set('RVB22 Current','D17','Earlier numerical inputs are historical where superseded by the frozen procurement set.');
  set('RVB22 Current','D20','Current exact source and output hashes: current/SOURCE_EFFECTIVITY.json.');
  set('RVB22 Current','A28','I25 fixed heat budget (W)');set('RVB22 Current','D28',2.940859375);
  set('RVB22 Current','D29','R155 PTFR0603B11K8N9, 11.8k; R156 PLT1206Z5051LBTS, 5.05k.');
  set('RVB22 Current','D30',result.electrical.main_normal_min_V);set('RVB22 Current','D32',0.25);
  set('RVB22 Current','A33','Stacked one-step board screen (C)');set('RVB22 Current','D33',result.thermal.stacked_board_screen_C);
  for(const sheet of ['Review Register','RVB22 Criteria','RVB22 Redlines','RVB22 Inputs','RVB22 Evidence']) {
    set(sheet,'A1',sheet+' — historical ledger');
    set(sheet,'A2','Pre-redline records retained. Current I32 substitutions, source hashes and affected verification supersede these records: analyses/i32/procurement_redline/README.md.');
  }
  set('RVB22 Gates','A1','I32 supplier and physical acceptance gates');
  set('RVB22 Gates','A2','Native/source gates below use I32 procurement evidence. Retained physical conditions require actual supplier or first-article acceptance.');
  set('RVB22 Gates','B5','CLOSED NATIVE I32');set('RVB22 Gates','C5','KiCad 9.0.9: zero ERC/DRC/unconnected/parity findings; 177 fitted STEP components; matching BOM, CPL, Gerber and drill outputs.');
  set('RVB22 Gates','B6','CLOSED BUILD 160 MHZ');set('RVB22 Gates','C6','Unchanged 32-file firmware source. The recovered 160 MHz target build retains 28/28 release checks.');
  set('RVB22 Gates','B7','PHYSICAL THERMAL CORRELATION');
  set('RVB22 Gates','C7','Updated 0.5/0.25 mm actual-copper screens retain the 2.940859375 W budget. Package, junction and immediate-air temperatures require physical correlation.');
  set('RVB22 Gates','D7','Retain the I25 workload, 65 C cabin, U201 air <=85 C and Adafruit 851 local <=60 C. Verify measured converter losses, cooling and package temperatures.');
  set('RVB22 Gates','C11','49 special vias and 15 um minimum finished plating retained. F101/U401 local; L121 factory catalog manual/wave process needs supplier approval.');
  set('RVB22 Gates','C14','177 fitted parts; 1,308 populated and 529 mated checks; 38 probe approaches. Full 1.71 mm height stack; no modeled interference.');
  wb.recalculate();
  console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!',options:{useRegex:true,maxResults:100},maxChars:2000})).ndjson);
  const changes=new Set(edits.map(x=>x.sheet+'!'+x.cell));
  function col(n){let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;}
  for(let i=0;i<19;i++) {const s=wb.worksheets.getItemAt(i),v=s.getUsedRange().values,f=s.getUsedRange().formulas,o=old[s.name];
    for(let r=0;r<o.values.length;r++)for(let c=0;c<o.values[r].length;c++) {
      const key=s.name+'!'+col(c)+(r+1);
      if(changes.has(key))continue;
      if(JSON.stringify(v[r]?.[c]??null)!==JSON.stringify(o.values[r][c]??null)||JSON.stringify(f[r]?.[c]??null)!==JSON.stringify(o.formulas[r]?.[c]??null))throw new Error('Unexpected cell change '+key);
    }
  }
  const preview=await wb.render({sheetName:'RVB22 Current',range:'A1:H13',scale:1,format:'png'});
  await fs.writeFile(root+'/analyses/i32/procurement_redline/review_register/after.png',new Uint8Array(await preview.arrayBuffer()));
  await (await SpreadsheetFile.exportXlsx(wb)).save(path);
  await fs.writeFile(dir+'/REVIEW_REGISTER_UPDATE.json',JSON.stringify({status:'TARGETED_CURRENT_EFFECTIVITY_UPDATE',sheets_preserved:19,unrelated_cell_values_and_formulas_unchanged:true,edits},null,2)+'\n');
  process.exit(0);
}
console.log((await wb.inspect({kind:'workbook,sheet,table',maxChars:6500,tableMaxRows:3,tableMaxCols:8,tableMaxCellChars:90})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'I32|I24|I21|SOURCE|Source|TNPU|R156|L121',options:{useRegex:true,maxResults:45},maxChars:8000})).ndjson);
const preview=await wb.render({sheetName:'RVB22 Current',range:'A1:H13',scale:1,format:'png'});
await fs.writeFile(root+'/analyses/i32/procurement_redline/review_register/before.png',new Uint8Array(await preview.arrayBuffer()));
