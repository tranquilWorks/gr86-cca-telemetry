
function hideErrorMessage(){$("#pms-res-error").hide(),$("#pms-nonstand-error").hide(),$("#error-low").hide(),$("#error-low-high").hide(),$("#error-med-low").hide(),$("#error-med-high").hide(),$("#error-high-low").hide(),$("#error-high-high").hide(),$("#temp-error").hide()}
function initialvalues(){$(".form")[0].reset(),$("#pms-pulse").text("Single Pulse Energy (Joules)"),$("#pms-res").hide(),$("#pms-res-val").show(),$("#pms-model").val(""),$("#pms-res-val").val(""),$("#amb_low").val(-55),$("#amb_med").val(70),$("#amb_high").val(125),$("#low-temp").text("-55 ℃"),$("#med-temp").text("70 ℃"),$("#high-temp").text("125 ℃"),$(".pms-ambTemp-table1").val("-55 ℃"),$(".pms-ambTemp-table2").val("70 ℃"),$(".pms-ambTemp-table3").val("125 ℃"),$(".low, .med, .high").val(""),$("#error-low").val(""),$("#error-low-high").val(""),$("#error-med-low").val(""),$("#error-med-high").val(""),$("#error-high-low").val(""),$("#error-high-high").val(""),$("#temp-error").val(""),$("#pms-res-error").text(""),$("#pms-nonstand-error").text(""),clearfields(),hideErrorMessage()}
function clearfields(){$("#pms-part-span").text(""),$("#pms-graphname").text(""),$("#pms-graph-error").show(),$("#pms-graph-error").addClass("graph-error-new"),$("#pms-product-page-link, #pms-datasheet-link, #pms-buy").prop("href","javascript:void(0);
"),$("#pms-resistance, #pms-power-rating, #pms-derated, #j-disp, #j-disp1, #j-dispRes, #pms-amps").text(""),$("#time, #time4, #time2, #time5, #time3, #time6, #time10, #time13, #time11, #time14, #time12, #time15").val(""),$("#rpResult1, #rpResult2, #rpResult3, #derated-power, #derated-power2, #derated-power3, #wj_result, #wj_result2, #wj_result3, #co1, #co2, #co3, #sto1-1result, #sto1-2result, #sto1-3result, #sto5-1result, #sto5-2result, #sto5-3result").val(""),$("#co1-2, #wj_result4, #wj_result7,#wj_result10, #sto1-1result1, #sto1-1result2, #co2-1, #wj2_result5, #wj2_result8, #wj2_result11, #sto1-2result2, #sto1-2result3, #co3-1, #wj3_result6, #wj3_result9, #wj3_result12, #sto1-3result2, #sto1-3result3").val(""),$("#powerW, #powerW3, #powerW6, #powerW9, #powerW12, #powerW-total, #currentA, #currentA3, #currentA6, #currentA9, #currentA12, #currentA-total, #powerW1, #powerW4, #powerW7, #powerW10, #powerW13, #powerW-total1").val(""),$("#currentA1, #currentA4, #currentA7, #currentA10, #currentA13, #currentA-total1, #powerW2, #powerW5, #powerW8, #powerW11, #powerW14, #powerW-total2, #currentA2, #currentA5, #currentA8, #currentA11, #currentA14, #currentA-total2").val("")}
function changeModel(){$("#pms-pulse").text("Single Pulse Energy (Joules)"),$("#pulse1").prop("checked",!0),$("#pms-res-val").val(""),hideErrorMessage(),clearfields(),""==$("#pms-model").val()&&($("#amb_low").val(-55),$("#amb_med").val(70),$("#amb_high").val(125),$("#low-temp").text("-55 ℃"),$("#med-temp").text("70 ℃"),$("#high-temp").text("125 ℃"),$(".pms-ambTemp-table1").val("-55 ℃"),$(".pms-ambTemp-table2").val("70 ℃"),$(".pms-ambTemp-table3").val("125 ℃"),$(".low, .med, .high").val(""))}
function addCommas(e){e+="",x=e.split("."),x1=x[0],x2=x.length>1?"."+x[1]:"";
for(var r=/(\d+)(\d{3})/;
r.test(x1);
)x1=x1.replace(r,"$1,$2");
return x1+x2}
function isNumber(e,r){var t=e.which?e.which:event.keyCode;
return 45==t&&-1==$(r).val().indexOf("-")||46==t&&-1==$(r).val().indexOf(".")||!(t>31)||!(t<48||t>57)}
function graph(){
function e(e,r,t,a){$('<div id="tooltip">'+t+"</div>").css({top:r+5,left:e+-100,"border-color":a,"z-index":"9999"}).appendTo("body").fadeIn(200)}var r=[],t=null;
$("#pms-graph").bind("plothover",function(a,o,l){if($("#x").text(o.x.toFixed(2)),$("#y").text(o.y.toFixed(2)),l){if(t!=l.datapoint){t=l.datapoint,$("#tooltip").remove();
var s=l.datapoint[0],i=l.datapoint[1],p=l.series.color;
content=l.series.label+" of "+s+" = "+i,r[l.dataIndex]&&(content=r[l.dataIndex].alternateText),e(l.pageX,l.pageY,"<b>"+l.series.label+"</b><br /> "+addCommas(i),p)}}else $("#tooltip").remove(),t=null}),$("#pms-graph").bind("plotclick",function(t,a,o){o&&o.dataIndex<2&&(o.alternateText=0==o.dataIndex?"hello":"bye",r[o.dataIndex]=o,$("#tooltip").remove(),e(o.pageX,o.pageY,o.alternateText))})}
function canvas(){if($("#pulse1").is(":checked")){graph(),$("#pms-pulse").text("Single Pulse Energy (Joules)");
var e=$("#wj_result").val(),r=$("#sto1-1result").val(),t=$("#sto1-1result2").val(),a=$("#wj_result2").val(),o=$("#sto1-2result").val(),l=$("#sto1-2result3").val(),s=$("#wj_result3").val(),i=$("#sto1-3result").val(),p=$("#sto1-3result3").val(),n=$("#co1").val(),d=$("#co2").val(),m=$("#co3").val(),u=[[1e-5,e],[1e-4,e],[n,e],[1,r],[5,t]],v=[[1e-5,a],[1e-4,a],[d,a],[1,o],[5,l]],c=[[1e-5,s],[1e-4,s],[m,s],[1,i],[5,p]],h={grid:{markings:markings,backgroundColor:"#fff",hoverable:!0,color:"#000",borderColor:"#333",borderWidth:{top:2,right:2,bottom:2,left:2},hoverable:!0,clickable:!0},valueLabels:{show:!0},yaxis:{ticks:[.001,.01,.1,1,10,100,1e3],transform:function(e){return 0===e?0:Math.log(1e3*e)},inverseTransform:function(e){return Math.exp(e)},tickDecimals:3},xaxis:{ticks:[1e-5,1e-4,.001,.01,.1,1,10],transform:function(e){return 0===e?0:Math.log(e+0)},inverseTransform:function(e){return Math.exp(e)},tickFormatter:function(e,r){return"1.0E"+Math.round(+Math.log(e)/Math.LN10).toString()}},series:{lines:{show:!0},dataLabels:!0,points:{radius:3,show:!1,fill:!0}}};
$.plot($("#pms-graph"),[{data:u,color:"#accae8",label:"Low Ambient Temperature"},{data:v,color:"#96c789",label:"Standard Ambient Temperature"},{data:c,color:"#eb595c",label:"Maximum Ambient Temperature"}],h)}else if($("#pulse2").is(":checked")){$("#pms-pulse").text("Single Pulse Power (Watts)");
var g=$("#wj_result4").val(),w=$("#time").val(),x=g/w,f=x,b=$("#powerW6").val(),F=b.replace(/\,/g,""),_=$("#wj2_result5").val(),y=$("#time2").val(),M=_/y,j=M,T=$("#powerW7").val(),A=T.replace(/\,/g,""),W=$("#wj3_result6").val(),k=$("#time3").val(),E=W/k,R=E,C=$("#powerW8").val(),S=C.replace(/\,/g,""),P=(n=$("#co1").val(),d=$("#co2").val(),m=$("#co3").val(),[[1e-5,f],[n,F],[1,F],[5,F]]),L=[[1e-5,j],[d,A],[1,A],[5,A]],q=[[1e-5,R],[m,S],[1,S],[5,S]];
h={series:{lines:{show:!0},points:{radius:3,show:!1,fill:!0}},grid:{markings:markings,backgroundColor:"#fff",hoverable:!0,color:"#000",borderColor:"#333",borderWidth:{top:2,right:2,bottom:2,left:2},hoverable:!0,clickable:!0},valueLabels:{show:!0},yaxis:{ticks:[0,1,10,100,1e3,1e4,1e5,1e6,1e7],transform:function(e){return 0===e?0:Math.log(100*e)},inverseTransform:function(e){return Math.exp(e)},tickFormatter:function(e){return e.toString().replace(/\B(?=(?:\d{3})+(?!\d))/g,",")}},axisY:{interval:20},xaxis:{ticks:[1e-5,1e-4,.001,.01,.1,1,10],transform:function(e){return 0===e?0:Math.log(e+0)},inverseTransform:function(e){return Math.exp(e)},tickFormatter:function(e,r){return"1.0E"+Math.round(+Math.log(e)/Math.LN10).toString()}}};
jQuery.plot($("#pms-graph"),[{data:P,color:"#accae8",label:"Low Ambient Temperature"},{data:L,color:"#96c789",label:"Standard Ambient Temperature"},{data:q,color:"#eb595c",label:"Maximum Ambient Temperature"}],h)}}
function plotline(){canvas(),$("#pms-graph-error").removeClass("graph-error-new"),$("#pms-graph-error").hide(),$("#temp-error").hide()}
function isValidRange(e,r){$.ajax({method:"GET",url:"/api/designtools/calculator-power-metal-strip/calculator-pms/?type=getPMSValidRange&model="+e+"&res="+r}).done(function(e){0===e.length?(clearfields(),$("#pms-res-error").text("Resistance value is out of range"),$("#pms-res-error").show()):(ambient_temp(),$("#pms-res-error").hide()),isNonStandard(r)})}
function isNonStandard(e){decades=$.ajax({method:"GET",url:"/api/designtools/calculator-power-metal-strip/calculator-pms?type=getPMSDecade&enteredRes="+e}),decades.done(function(e){0===e.length?($("#pms-nonstand-error").text("Non-Standard"),$("#pms-nonstand-error").show()):$("#pms-nonstand-error").hide()})}
function ambient_temp(){var e,r=$(".low").val(),t=$(".med").val(),a=$(".high").val(),o=$("#amb_low"),l=$("#amb_med"),s=$("#amb_high"),i=$("#pms-model").val(),p=$("#pms-res-val").val(),n=$("#pms-res").val(),d=-65;
""==r&&(r=-55),""==t&&(t=70),""==a&&(a=125);
var m=$("#pms-model").find(":selected").attr("type");
"Range"==m?(e=p,getMaxTemp=$.ajax({method:"GET",url:"/api/designtools/calculator-power-metal-strip/calculator-pms?type=getPMSValuesRange&model="+i+"&res="+e})):"Discrete"==m&&(e=n,getMaxTemp=$.ajax({method:"GET",url:"/api/designtools/calculator-power-metal-strip/calculator-pms?type=getValuesDiscrete&model="+i+"&resVal="+e})),getMaxTemp.done(function(e){var i;
"Range"==m?i=e[0].max_op_temp:"Discrete"==m&&(i=e[0].node.operatingTemp),r<d?($("#error-low").text("out of range low"),$("#error-low").show(),$("#temp-error").text("Temperature is out of range for product selected"),$("#temp-error").show(),$("#error-low-high").hide(),o.val(""),$("#low-temp").text(r+" ℃"),$(".pms-ambTemp-table1").val(r+" ℃")):r>i?($("#error-low").hide(),$("#error-low-high").text("out of range high"),$("#temp-error").text("Temperature is out of range for product selected"),$("#error-low-high").show(),$("#temp-error").show(),o.val(""),$("#low-temp").text(r+" ℃"),$(".pms-ambTemp-table1").val(r+" ℃")):($("#error-low").hide(),$("#error-low-high").hide(),o.val(r),$("#low-temp").text(r+" ℃"),$(".pms-ambTemp-table1").val(r+" ℃")),t<d?($("#error-med-high").hide(),$("#error-med-low").text("out of range low"),$("#error-med-low").show(),$("#temp-error").text("Temperature is out of range for product selected"),$("#temp-error").show(),l.val(""),$("#med-temp").text(t+" ℃"),$(".pms-ambTemp-table2").val(t+" ℃")):t>i?($("#error-med-low").hide(),$("#error-med-high").text("out of range high"),$("#error-med-high").show(),$("#temp-error").text("Temperature is out of range for product selected"),$("#temp-error").show(),l.val(""),$("#med-temp").text(t+" ℃"),$(".pms-ambTemp-table2").val(t+" ℃")):($("#error-med-low").hide(),$("#error-med-high").hide(),l.val(t),$("#med-temp").text(t+" ℃"),$(".pms-ambTemp-table2").val(t+" ℃")),a<d?($("#error-high-high").hide(),$("#error-high-low").text("out of range low"),$("#error-high-low").show(),$("#temp-error").text("Temperature is out of range for product selected"),$("#temp-error").show(),s.val(""),$("#high-temp").text(a+" ℃"),$(".pms-ambTemp-table3").val(a+" ℃")):a>i?($("#error-high-low").hide(),$("#error-high-high").text("out of range high"),$("#error-high-high").show(),$("#temp-error").text("Temperature is out of range for product selected"),$("#temp-error").show(),s.val(""),$("#high-temp").text(a+" ℃"),$(".pms-ambTemp-table3").val(a+" ℃")):($("#error-high-low").hide(),$("#error-high-high").hide(),s.val(a),$("#high-temp").text(a+" ℃"),$(".pms-ambTemp-table3").val(a+" ℃")),""==o.val()&&""==l.val()&&""==s.val()||compute(o.val(),l.val(),s.val())})}
function compute(e,r,t){var a,o,l,s=25,i=70,p=325,n=1e-5,d=1,m=5,u=$("#pms-model").val(),v=$("#pms-res-val").val(),c=$("#pms-res").val(),h=$("#amb_low").val(),g=$("#amb_med").val(),w=$("#amb_high").val(),x=$("#pms-model").find(":selected").attr("type");
clearfields(),"Discrete"==x?(a=c,getValuesRange=$.ajax({method:"GET",url:"/api/designtools/calculator-power-metal-strip/calculator-pms?type=getPMSValuesDiscrete&model="+u+"&resVal="+a}),getHyperlink(u,a)):"Range"==x&&(a=v,getValuesRange=$.ajax({method:"GET",url:"/api/designtools/calculator-power-metal-strip/calculator-pms?type=getPMSValuesRange&model="+u+"&res="+a}),getHyperlink(u,"")),getValuesRange.done(function(u){var v=u[0].product_joule,c=u[0].max_op_temp,x=u[0].power_rating,f=u[0].overload_factor,b=$("#pms-model").find(":selected").attr("type");
wire_energy="Range"==b?v*a:v;
var F=[[c-h]/[c-i]*100],_=[[c-g]/[c-i]*100],y=[[c-w]/[c-i]*100],M=(F/100*x).toFixed(5),j=(_/100*x).toFixed(5),T=(y/100*x).toFixed(5);
if(""!=e){if(F>=100){$("#rpResult1").val(100);
var A=(1*x).toFixed(3);
$("#derated-power").val(A)}else $("#rpResult1").val(Math.round(F)),$("#derated-power").val(M);
wireEnergyLow=[[p-[h-s]]/p]*[wire_energy],wj_result_low=parseFloat(wireEnergyLow).toFixed(3),$("#wj_result, #wj_result4, #wj_result7, #wj_result10").val(wj_result_low),power_low=[wireEnergyLow/n],$("#powerW, #powerW3").val(addCommas(Math.round(power_low)))}if(""!=r){if(_>=100){$("#rpResult2").val(100);
var W=(1*x).toFixed(3);
$("#derated-power2").val(W)}else $("#rpResult2").val(Math.round(_)),$("#derated-power2").val(j);
wireEnergyMed=[[p-[g-s]]/p]*[wire_energy],wj_result_med=parseFloat(wireEnergyMed).toFixed(3),$("#wj_result2, #wj2_result5, #wj2_result8, #wj2_result11").val(wj_result_med),o=[wireEnergyMed/n],$("#powerW1, #powerW4").val(addCommas(Math.round(o)))}if(""!=t){if(y>=100){$("#rpResult3").val(100);
var k=(1*x).toFixed(3);
$("#derated-power3").val(k),l=k}else $("#rpResult3").val(Math.round(y)),$("#derated-power3").val(T),l=T;
wireEnergyHigh=[[p-[w-s]]/p]*[wire_energy],wj_result_high=parseFloat(wireEnergyHigh).toFixed(3),$("#wj_result3, #wj3_result6, #wj3_result9, #wj3_result12").val(wj_result_high),power_high=[wireEnergyHigh/n],$("#powerW2, #powerW5").val(addCommas(Math.round(power_high)))}if(""!=$("#derated-power").val()){var E=parseFloat($("#derated-power").val()),R=E*f;
R<wireEnergyLow&&(R=wireEnergyLow);
var C=parseFloat(R).toFixed(1);
$("#sto1-1result").val(C);
var S=5*R,P=parseFloat(S).toFixed(1);
$("#sto5-1result").val(P);
var L=R.toFixed(2);
$("#sto1-1result1").val(L);
var q=S.toFixed(2);
$("#sto1-1result2").val(q);
var N=[wireEnergyLow/R],D=parseFloat(N).toFixed(4);
$("#co1, #co1-2").val(D),$("#time, #time4").val("0.000010"),$("#time10").val("1"),$("#time13").val("5");
var V=[wireEnergyLow/N],G=parseFloat(V).toFixed(1);
$("#powerW6").val(addCommas(G));
var H=[R/d],O=parseFloat(H).toFixed(1);
$("#powerW9").val(addCommas(O));
var I=[V/10],J=parseFloat(I).toFixed(1);
$("#powerW-total").val(J);
var X=[S/m],Y=parseFloat(X).toFixed(1);
$("#powerW12").val(Y);
var U=Math.sqrt([power_low/a]);
$("#currentA, #currentA3").val(addCommas(Math.round(U)));
var z=Math.sqrt([V/a]),B=parseFloat(z).toFixed(1);
$("#currentA6").val(addCommas(B));
var Q=Math.sqrt([H/a]),K=parseFloat(Q).toFixed(1);
$("#currentA9").val(addCommas(K));
var Z=Math.sqrt([X/a]),ee=parseFloat(Z).toFixed(1);
$("#currentA12").val(addCommas(ee));
var re=Math.sqrt([I/a]),te=parseFloat(re).toFixed(1);
$("#currentA-total").val(addCommas(te))}if(""!=$("#derated-power2").val()){var ae=parseFloat($("#derated-power2").val()),oe=ae*f;
oe<wireEnergyMed&&(oe=wireEnergyMed);
var le=parseFloat(oe).toFixed(1);
$("#sto1-2result").val(le);
var se=5*oe,ie=parseFloat(se).toFixed(1);
$("#sto5-2result").val(ie);
var pe=oe.toFixed(2);
$("#sto1-2result2").val(pe);
var ne=se.toFixed(2);
$("#sto1-2result3").val(ne);
var de=[wireEnergyMed/oe],me=parseFloat(de).toFixed(4);
$("#co2, #co2-1").val(me),$("#time2, #time5").val("0.000010"),$("#time11").val("1"),$("#time14").val("5");
var ue=[wireEnergyMed/de],ve=parseFloat(ue).toFixed(1);
$("#powerW7").val(addCommas(ve));
var ce=[oe/d],he=parseFloat(ce).toFixed(1);
$("#powerW10").val(addCommas(he));
var $e=[ue/10],ge=parseFloat($e).toFixed(1);
$("#powerW-total1").val(ge);
var we=[se/m],xe=parseFloat(we).toFixed(1);
$("#powerW13").val(xe);
var fe=Math.sqrt([o/a]);
$("#currentA1, #currentA4").val(addCommas(Math.round(fe)));
var be=Math.sqrt([ue/a]),Fe=parseFloat(be).toFixed(1);
$("#currentA7").val(addCommas(Fe));
var _e=Math.sqrt([ce/a]),ye=parseFloat(_e).toFixed(1);
$("#currentA10").val(addCommas(ye));
var Me=Math.sqrt([we/a]),je=parseFloat(Me).toFixed(1);
$("#currentA13").val(addCommas(je));
var Te=Math.sqrt([$e/a]),Ae=parseFloat(Te).toFixed(1);
$("#currentA-total1").val(addCommas(Ae))}if(""!=$("#derated-power3").val()){var We=parseFloat($("#derated-power3").val()),ke=We*f;
ke<wireEnergyHigh&&(ke=wireEnergyHigh);
var Ee=parseFloat(ke).toFixed(1);
$("#sto1-3result").val(Ee);
var Re=5*ke,Ce=parseFloat(Re).toFixed(1);
$("#sto5-3result").val(Ce);
var Se=ke.toFixed(2);
$("#sto1-3result2").val(Se);
var Pe=Re.toFixed(2);
$("#sto1-3result3").val(Pe);
var Le=[wireEnergyHigh/ke],qe=parseFloat(Le).toFixed(4);
$("#co3, #co3-1").val(qe),$("#time3, #time6").val("0.000010"),$("#time12").val("1"),$("#time15").val("5");
var Ne=[wireEnergyHigh/Le],De=parseFloat(Ne).toFixed(1);
$("#powerW8").val(addCommas(De));
var Ve=[ke/d],Ge=parseFloat(Ve).toFixed(1);
$("#powerW11").val(addCommas(Ge));
var He=[Ne/10],Oe=parseFloat(He).toFixed(1);
$("#powerW-total2").val(Oe);
var Ie=[Re/m],Je=parseFloat(Ie).toFixed(1);
$("#powerW14").val(Je);
var Xe=Math.sqrt([power_high/a]);
$("#currentA2, #currentA5").val(addCommas(Math.round(Xe)));
var Ye=Math.sqrt([Ne/a]),Ue=parseFloat(Ye).toFixed(1);
$("#currentA8").val(addCommas(Ue));
var ze=Math.sqrt([Ve/a]),Be=parseFloat(ze).toFixed(1);
$("#currentA11").val(addCommas(Be));
var Qe=Math.sqrt([Ie/a]),Ke=parseFloat(Qe).toFixed(1);
$("#currentA14").val(addCommas(Ke));
var Ze=Math.sqrt([He/a]),er=parseFloat(Ze).toFixed(1);
$("#currentA-total2").val(addCommas(er))}graphLabels(l,x,o),""!=$("#amb_low").val()&&""!==$("#amb_med").val()&&""!==$("#amb_high").val()?plotline():$("#pms-graph-error").show()})}
function partNumber(){var e,r,t,a,o,l,s=$("#pms-model option:selected").text(),i=$("#pms-res-val").val(),p=$("#pms-res").val(),n=$("#pms-model").find(":selected").attr("type");
"Discrete"==n?e=p:"Range"==n&&(e=i);
var d=s.substring(0,8),m=d.replace(/\.+$/,"");
e<.001?(t=[1e3*e],res_parse=parseFloat(t).toFixed(3),res_parseSecondIndex=res_parse.toString().substr(1),o=res_parseSecondIndex.replace(res_parseSecondIndex.charAt(0),"L"),l=o.substring(0,5),r=s+l+"0xyy"):e<.01?s.indexOf("...18")>=0?(t=[1e3*e],res_parse=parseFloat(t).toFixed(3),o=res_parse.toString().replace(res_parse.toString().charAt(1),"L"),r=m+o+"xyy"):(t=[1e3*e],res_parse=parseFloat(t).toFixed(3),o=res_parse.toString().replace(res_parse.toString().charAt(1),"L"),r=s+o+"xyy"):1==e?r=s+"1R000":s.indexOf("...18")>=0?(a=parseFloat(e).toFixed(4),o=a.toString().replace(a.toString().charAt(1),"R"),r=m+o.substring(1,6)+"xyy"):(a=parseFloat(e).toFixed(4),o=a.toString().replace(a.toString().charAt(1),"R"),r=s+o.substring(1,6)+"xyy"),$("#pms-part-span").text(r),""!=r&&buyNow(r)}
function partNumberLbl(){var e,r=$("#pms-part-span").text(),t=$("#pms-model").val();
e=t.indexOf(".")>=0&&"18"!=r.substr(r.length-2)?r+"18":r,$("#pms-part-span").text(e),$("#pulse1").is(":checked")?$("#pms-graphname").text("PULSE ENERGY OF "+e):$("#pulse2").is(":checked")&&$("#pms-graphname").text("PULSE POWER OF "+e)}
function buyNow(e){if($("#pulse1").is(":checked")||$("#pulse2").is(":checked")){var r=window.location.origin;
if(""!=e){var t=e.split("xyy")[0];
$("#pms-buy").prop("href",r+"/search?query="+t+"&search-inventory-submit.x=0&search-inventory-submit.y=0&type=inv")}}}for(var markings=[],abscissa=[.2,.3,.39,.49,.59,.69,.8,.9,1],additionalPoints=[2.05,3.15,4.24,5.34,6.44,7.54,8.65,9.75,9.85],power=4;
power>=0;
){for(var i=0;
i<abscissa.length;
i++){var value=abscissa[i]/Math.pow(10,power);
markings.push({color:"#ccc",lineWidth:1,xaxis:{from:value,to:value}})}power--}for(i=0;
i<additionalPoints.length;
i++)markings.push({color:"#ccc",lineWidth:1,xaxis:{from:additionalPoints[i],to:additionalPoints[i]}});
var calculator={getModels:function(){$("#pms-model").on("change",function(e){var r=$("#pms-model").find(":selected").attr("type"),t=$(this),a=$("select").index(t);
"Discrete"===r?($("#pms-res-val").hide(),$("#pms-res").show(),""!=t.val()&&(getResistance(t.val()),$("#pms-model").not(":eq("+a+")").find(":first").prop("selected",!0))):($("#pms-res").hide(),$("#pms-res-val").show()),changeModel()})}},getResistance=function(e){$.ajax({method:"GET",url:"/api/designtools/calculator-power-metal-strip/calculator-pms?type=getPMSRange&model="+e}).done(function(e){$("select#pms-res > option").remove(),e.forEach(function(e){var r=e.resVal;
$("select#pms-res").append("<option value="+r+">"+r+"</option>")})})},getHyperlink=function(e,r){hyperlink=""==r?$.ajax({method:"GET",url:"/api/designtools/calculator-power-metal-strip/calculator-pms?type=getDocRange&model="+e}):$.ajax({method:"GET",url:"/api/designtools/calculator-power-metal-strip/calculator-pms?type=getDocDiscrete&model="+e+"&resVal="+r}),hyperlink.done(function(e){var r=e,t="/product/";
$("#pms-product-page-link").prop("href","/"+__NEXT_DATA__.props.pageProps.pathLanguage+t+r);
var a="http://www.vishay.com/doc?";
$("#pms-datasheet-link").prop("href",a+r)})},graphLabels=function(e,r,t){var a,o=$("#pms-res-val").val(),l=$("#pms-res").val(),s=$("#pms-model").find(":selected").attr("type");
a="Range"==s?o:l,$("#pms-resistance").text(a).append(" &#8486;
"),$("#pms-power-rating").text(r+" W @ 70").append(" &#x2103;
");
var i=parseFloat(e),p=i.toFixed(2),n=$("#amb_high").val();
p.indexOf("NaN")<0&&$("#pms-derated").text(p+" W @ ").append(n+" &#x2103;
");
var d=addCommas(Math.round(t)),m=Math.sqrt([t/a]),u=m.toFixed(1),v=addCommas(Math.round(u)),c=$("#amb_med").val();
if(d.indexOf("NaN")<0){var h=$("#wj2_result11").val();
$("#j-disp").text(h).append(" J / ");
var g=parseFloat($("#time5").val());
$("#j-disp1").text(g).append(" s = "),$("#j-dispRes").text(d).append(" W @ "+c+" &#x2103;
"),$("#pms-amps").text(v).append(" A")}partNumber(),partNumberLbl()};
$(document).ready(function(e){calculator.getModels(),initialvalues(),e("#pms-res-val, .low, .med, .high").keypress(function(e){return isNumber(e,this)}),e("#pms-btn-reset").click(function(){initialvalues()}),e("#pms-btn-compute").click(function(){var r=e("#pms-model").find(":selected").attr("type"),t=e("#pms-model").val(),a=e("#pms-res-val").val();
"Range"==r?a>1||""==a?(alert("Please enter a decimal value equal to or less than 1."),e("#pms-res-error").text("Resistance value is out of range"),e("#pms-res-error").show()):(e("#pms-res-error").hide(),isValidRange(t,a)):"Discrete"==r&&ambient_temp()}),e("#pms-res-val").keyup(function(r){if(13==r.keyCode){var t=e("#pms-model").val(),a=e("#pms-res-val").val();
""!=e("#pms-model").val()&&(e(this).val()>1||""==e(this).val()?(alert("Please enter a decimal value equal to or less than 1."),e("#pms-res-error").text("Resistance value is out of range"),e("#pms-res-error").show()):(e("#pms-res-error").hide(),isValidRange(t,a)))}}),e(".low, .med, .high").keyup(function(r){if(13==r.which&&""!=e("#pms-model").val()){var t=e("#pms-model").find(":selected").attr("type"),a=e("#pms-model").val(),o=e("#pms-res-val").val();
"Range"==t?""!=o&&(o>1||""==o?(alert("Please enter a decimal value equal to or less than 1."),e("#pms-res-error").text("Resistance value is out of range"),e("#pms-res-error").show()):(e("#pms-res-error").hide(),isValidRange(a,o))):"Discrete"==t&&ambient_temp()}}),e("#pulse1, #pulse2").click(function(){""==e("#powerW6").val()&&""==e("#powerW7").val()&&""==e("#powerW8").val()||(partNumberLbl(),""!=e("#amb_low").val()&&""!=e("#amb_med").val()&&""!=e("#amb_high").val()&&(plotline(),e("#pulse1").is(":checked")?e("#pms-pulse").text("Single Pulse Energy (Joules)"):e("#pulse2").is(":checked")&&e("#pms-pulse").text("Single Pulse Power (Watts)")))}),e("#pms-btn-sales").on("click",function(){window.open("/"+__NEXT_DATA__.props.pageProps.pathLanguage+"/company/contacts/","_blank")}),e("#pms-btn-help").on("click",function(){var e="ww2bresistors@vishay.com",r="Power Metal Strip Pulse Calculator Tool";
window.location="mailto:"+e+"?subject="+r})});
