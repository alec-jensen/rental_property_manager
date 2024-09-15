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
        if (data.valid === true) {
						return true;
				}
    } catch (err) {
        console.error(err);
        return false;
    }
}

export function logout() {
		fetch(`${API_URL}/user/logout`, {
				method: 'POST',
				headers: {
						'Content-Type': 'application/json',
				},
				body: JSON.stringify({
						session_id: localStorage.getItem('session_id'),
						session_token: localStorage.getItem('session_token'),
				}),
		})
		.then((res) => res.json())
		.then((data) => {
				if (data.success) {
						window.location.href = '/authentication/sign-in';
				}
		})
		.catch((err) => {
				console.error(err);
		});
}

export async function getUserData() {
	if (!localStorage.getItem('session_id') || !localStorage.getItem('session_token')) {
			window.location.href = '/authentication/sign-in';
			return;
	}

	try {
			const response = await fetch(`${API_URL}/user/@me`, {
					method: 'GET',
					headers: {
							'Content-Type': 'application/json',
							Authorization: `Bearer ${localStorage.getItem('session_id')}:${localStorage.getItem('session_token')}`,
					},
			});

			if (!response.ok) {
					throw new Error('Network response was not ok');
			}

			const data = await response.json();
			return data;
	} catch (err) {
			console.error(err);
			return null;
	}
}
