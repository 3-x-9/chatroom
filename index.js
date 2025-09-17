console.log("hey")

const URL = "ws://localhost:8005"

const ws = new WebSocket(URL)
const form = document.querySelector('form')
const messageList = document.querySelector('#messages')
const text_area = document.querySelector("#text_input")

ws.onopen = (event) =>{
    console.log("Connection established")

}

ws.onmessage = (event) =>{
    console.log("Received raw:", event.data);
    const eventData = JSON.parse(event.data)
    const message = `
    <div class="message">
        <p><b>${eventData.username}</b> : ${eventData.body}</p>
    </div>`

    messageList.innerHTML += message

    console.log("Message: ", eventData)
    messageList.scrollTop = messageList.scrollHeight;
}

ws.onclose = (event) =>{
    console.log("Connection closed")
}

ws.onerror = (event) =>{
    console.log("Connection error")
}

form.addEventListener('submit', (event) => {
    event.preventDefault();

    sendMessage();
})

text_area.addEventListener('keydown', (event) => {
    if (event.key == 'Enter' && !event.shiftKey){
        event.preventDefault();

        sendMessage();
    }
})

function sendMessage() {
    const formData = new FormData(form);
    const message = formData.get('text_input');
    ws.send(message);
    form.reset();
}
