export const API_URL = 'http://localhost:8000';

export async function testSession() {
    if (!localStorage.getItem('session_id') || !localStorage.getItem('session_token')) {
        return false;
    }

    try {
        const response = await fetch(`${API_URL}/user/check_session`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: localStorage.getItem('session_id'),
                session_token: localStorage.getItem('session_token'),
            }),
        });
        const data = await response.json();
        return data.valid;
    } catch (err) {
        console.error(err);
        return false;
    }
}

export function getUserData() {
    if (!localStorage.getItem('session_id') || !localStorage.getItem('session_token')) {
        window.location.href = '/authentication/sign-in';
    }

    fetch(`${API_URL}/user`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('session_id')}::${localStorage.getItem('session_token')}`,
        },
    })
    .then((res) => res.json())
    .then((data) => data)
    .catch((err) => {
        console.error(err);
    });
}
