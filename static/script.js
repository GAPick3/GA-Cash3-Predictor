const a=document.querySelector('input[name="alpha"]');
const b=document.querySelector('input[name="beta"]');
const c=document.querySelector('input[name="gamma"]');
[a,b,c].forEach(el=>{
  el.oninput = ()=> {
    document.getElementById('val_'+el.name).textContent = parseFloat(el.value).toFixed(2);
  };
});
