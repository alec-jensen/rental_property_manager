export const API_URL = 'http://localhost:8000';

function checkStoredSession() {
	if (
		localStorage.getItem('session_id') &&
		localStorage.getItem('session_token')
	) {
		return true;
	}

	return false;
}

export async function testSession() {
	if (!checkStoredSession()) {
		return false;
	}

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

	return false;
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
		});
}

export async function getUserData() {
	if (!checkStoredSession()) {
		window.location.href = '/authentication/sign-in';
		return;
	}

	const response = await fetch(`${API_URL}/user/@me`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${localStorage.getItem(
				'session_id',
			)}:${localStorage.getItem('session_token')}`,
		},
	});

	if (!response.ok) {
		throw new Error('Network response was not ok');
	}

	const data = await response.json();
	return data;
}

export async function getUsers(limit, offset) {
	if (!checkStoredSession()) {
		window.location.href = '/authentication/sign-in';
		return;
	}

	const response = await fetch(
		`${API_URL}/users?limit=${limit}&offset=${offset}`,
		{
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${localStorage.getItem(
					'session_id',
				)}:${localStorage.getItem('session_token')}`,
			},
		},
	);

	if (!response.ok) {
		throw new Error('Network response was not ok');
	}

	const data = await response.json();
	return data;
}

export async function updateUser(user_id, data) {
	if (!checkStoredSession()) {
		window.location.href = '/authentication/sign-in';
		return;
	}

	const response = await fetch(`${API_URL}/user/${user_id}/update`, {
		method: 'PATCH',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${localStorage.getItem(
				'session_id',
			)}:${localStorage.getItem('session_token')}`,
		},
		body: JSON.stringify(data),
	});

	const res = await response.json();
	return {response: response, data: res};
}
