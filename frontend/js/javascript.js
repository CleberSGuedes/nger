async function login() {
    const usuario = document.getElementById('usuario').value;
    const senha = document.getElementById('senha').value;

    const response = await fetch('http://127.0.0.1:5000/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ usuario, senha }),
    });

    const data = await response.json();
    const messageElement = document.getElementById('login-msg');

    if (response.ok) {
        messageElement.style.color = 'green';
        messageElement.textContent = data.message;
        // Aqui você pode redirecionar para outra página ou atualizar a interface
    } else {
        messageElement.style.color = 'red';
        messageElement.textContent = data.message;
    }
}
