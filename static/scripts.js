function createPoll() {
    const title = document.getElementById("title").value;
    const options = document.getElementById("options").value.split(",").map(option => option.trim());
    const pollData = {
        "title": title,
        "options": options
    };

    fetch('/polls/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(pollData),
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById("response").innerHTML = data.message;
            const redirectLink = document.getElementById("redirect");
            redirectLink.style.display = "block";
            redirectLink.href = 'https://poll-self-dev.koyeb.app/polls/' + data.poll_slug;
        })
        .catch(error => console.error(error));
}

document.addEventListener('DOMContentLoaded', function() {
    const submitBtn = document.getElementById('poll-data-submit');

    fetch('/whoami/')
        .then(response => {
            if (response.status === 403) {
                submitBtn.disabled = true;
                alert("Please enter your name to create a poll");
            } else {
                return response.json().then(data => {
                    const modal = document.getElementById('modal');
                    modal.style.display = 'none';
                    alert(`Welcome back! ${data.username}`);
                });
            }
        });
}, false);

function enterName() {
    const submitBtn = document.getElementById('poll-data-submit');
    const nameInput = document.getElementById('nameInput').value;
    if (nameInput.trim() !== '') {
        const data = {
            name: nameInput
        };

        fetch('/create_session/' + nameInput, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (response.ok) {
                const modal = document.getElementById('modal');
                modal.style.display = 'none';
                submitBtn.disabled = false;
                location.reload();
            } else {
                console.error('Error creating session');
            }
        })
        .catch(error => {
            console.error('An error occurred:', error);
        });
    }
}
