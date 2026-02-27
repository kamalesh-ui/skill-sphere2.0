// ---------- Mode Options ----------
const modeSelect = document.getElementById("mode");
const modes = ["python","java","c","c++","web","error","mongodb"];

const languageMap = {
    "python": "python",
    "java": "java",
    "c": "c",
    "c++": "cpp",
    "web": "html",
    "error": "plaintext",
    "mongodb": "json"
};

modes.forEach(m=>{
    let opt=document.createElement("option");
    opt.value=m;
    opt.innerText=m;
    modeSelect.appendChild(opt);
});

modeSelect.value = localStorage.getItem("defaultMode") || "python";

modeSelect.addEventListener("change", ()=>{
    const lang = languageMap[modeSelect.value];
    if(editor)
        monaco.editor.setModelLanguage(editor.getModel(), lang);
    localStorage.setItem("defaultMode", modeSelect.value);
});

// ---------- CHAT ----------
const chatBox=document.getElementById("chat");
const sendBtn=document.getElementById("sendBtn");

function addMessage(role,text){
    let div=document.createElement("div");
    div.classList.add("message",role);
    div.innerText=text;
    chatBox.appendChild(div);
    chatBox.scrollTop=chatBox.scrollHeight;
}

function typingAnimation(){
    let div=document.createElement("div");
    div.id="typing";
    div.classList.add("message","assistant");
    div.innerText="Typing...";
    chatBox.appendChild(div);
}

function removeTyping(){
    let t=document.getElementById("typing");
    if(t) t.remove();
}

function sendMessage(){
    let input=document.getElementById("message");
    let message=input.value.trim();
    let mode=modeSelect.value;

    if(!message) return;

    addMessage("user",message);
    typingAnimation();

    fetch("/chat",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({message,mode})
    })
    .then(res=>res.json())
    .then(data=>{
        removeTyping();
        addMessage("assistant", data.reply || "No response");
    })
    .catch(err=>{
        removeTyping();
        addMessage("assistant","⚠️ Server error");
        console.error(err);
    });

    input.value="";
}

// send button
sendBtn.addEventListener("click",sendMessage);

// ENTER key send
document.getElementById("message")
.addEventListener("keypress",e=>{
    if(e.key==="Enter") sendMessage();
});


// ---------- MONACO ----------
var editor;
require.config({
    paths:{'vs':'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs'}
});

require(['vs/editor/editor.main'],function(){
    editor=monaco.editor.create(document.getElementById('editor'),{
        value:'print("Hello Student!")',
        language:'python',
        theme:'vs-dark',
        automaticLayout:true
    });
});


// ---------- RUN CODE ----------
document.getElementById("runBtn").addEventListener("click",()=>{
    fetch("/run_code",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
            code:editor.getValue(),
            mode:modeSelect.value
        })
    })
    .then(res=>res.json())
    .then(data=>{
        document.getElementById("output").innerText =
            data.output || data.error;
    });
});