export const status = {
	NO_ORCA_CLIENT: "No orca client",
	ANTHROPIC_API_KEY_NOT_SET: "Anthropic API key is not set",
	ANTHROPIC_API_KEY_INVALID: "Anthropic API key is invalid",
	ANTHROPIC_API_KEY_NO_CREDIT: "Anthropic API key has no credit",
	ANTHROPIC_VALID: "Anthropic API key is valid", // to satisfy typescript
	GITHUB_TOKEN_NOT_SET: "GitHub token is not set",
	GITHUB_TOKEN_INVALID: "GitHub token is invalid",
	GITHUB_USERNAME_NOT_SET: "GitHub username is not set",
	GITHUB_USERNAME_INVALID: "GitHub username is invalid",
	GITHUB_USERNAME_INCORRECT: "GitHub username is incorrect",
	GITHUB_VALID: "GitHub username and token are valid", // to satisfy typescript
} as const;

export const errorMessage = {
	NO_ORCA_CLIENT:
		"The Orca client is not available. Please restart the task. If the issue persists, restart the node.",
	ANTHROPIC_API_KEY_NOT_SET:
		"Your Anthropic API key is not set. Please use the task extension helper to set up your Anthropic API key correctly.",
	ANTHROPIC_API_KEY_INVALID:
		"Your Anthropic API key is invalid. Please use the task extension helper to set up your Anthropic API key correctly.",
	ANTHROPIC_API_KEY_NO_CREDIT:
		"Your Anthropic API key has no credit. Please add credits to your Anthropic account to continue.",
	ANTHROPIC_VALID: "Your Anthropic API key is valid and has credit.", // to satisfy typescript
	GITHUB_TOKEN_INVALID:
		"Your GitHub token is invalid. Please use the task extension helper to set up your GitHub token correctly.",
	GITHUB_TOKEN_NOT_SET:
		"Your GitHub token is not set. Please use the task extension helper to set up your GitHub token correctly.",
	GITHUB_USERNAME_INVALID:
		"Your GitHub username is invalid. Please use the task extension helper to set up your GitHub username correctly.",
	GITHUB_USERNAME_INCORRECT:
		"Your GitHub username is incorrect. Please double check your GitHub username and make sure it is from the same account as your GitHub token.",
	GITHUB_USERNAME_NOT_SET:
		"Your GitHub username is not set. Please use the task extension helper to set up your GitHub username correctly.",
	GITHUB_VALID: "Your GitHub username and token are valid.", // to satisfy typescript
} as const;

export type CheckStatus = {
	valid: boolean;
	status: keyof typeof status;
};
