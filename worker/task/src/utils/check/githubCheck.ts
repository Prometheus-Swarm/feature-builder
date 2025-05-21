import { CheckStatus } from "../../constants/checks";

export async function checkGitHub(
	username: string | undefined,
	token: string | undefined
): Promise<CheckStatus> {
	if (!username) {
		console.log("[GITHUB CHECK] ❌ GitHub username is not set");
		return {
			valid: false,
			status: "GITHUB_USERNAME_NOT_SET",
		};
	}

	if (!token) {
		console.log("[GITHUB CHECK] ❌ GitHub token is not set");
		return {
			valid: false,
			status: "GITHUB_TOKEN_NOT_SET",
		};
	}

	const isUsernameValid = await checkGitHubUsername(username);

	if (!isUsernameValid) {
		console.log("[GITHUB CHECK] ❌ GitHub username is invalid");
		return {
			valid: false,
			status: "GITHUB_USERNAME_INVALID",
		};
	}

	const isTokenValid = await checkGitHubToken(token);

	if (!isTokenValid) {
		console.log("[GITHUB CHECK] ❌ GitHub token is invalid");
		return {
			valid: false,
			status: "GITHUB_TOKEN_INVALID",
		};
	}
	const isIdentityValid = await checkGitHubIdentity(username, token);

	if (!isIdentityValid) {
		console.log("[GITHUB CHECK] ❌ GitHub identity is invalid");
		return {
			valid: false,
			status: "GITHUB_USERNAME_INCORRECT",
		};
	}

	console.log("[GITHUB CHECK] ✅ GitHub username and token are valid");
	return {
		valid: true,
		status: "GITHUB_VALID",
	};
}

async function checkGitHubUsername(username: string) {
	const res = await fetch(`https://api.github.com/users/${username}`);

	return res.status === 200;
}

async function checkGitHubToken(token: string) {
	const res = await fetch("https://api.github.com/user", {
		headers: {
			Authorization: `token ${token}`,
		},
	});

	return res.status === 200;
}

async function checkGitHubIdentity(username: string, token: string) {
	const res = await fetch("https://api.github.com/user", {
		headers: {
			Authorization: `token ${token}`,
			Accept: "application/vnd.github.v3+json",
		},
	});

	if (res.status !== 200) {
		return false;
	}

	const data = await res.json();

	if (data.login.toLowerCase() !== username.toLowerCase()) {
		return false;
	}

	return true;
}
