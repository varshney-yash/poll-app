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
            redirectLink.href = 'localhost:8000/polls/' + data.poll_slug;
        })
        .catch(error => console.error(error));
}
