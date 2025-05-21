import { CheckStatus } from "../../constants/checks";

export async function checkAnthropic(
	apiKey: string | undefined
): Promise<CheckStatus> {
	if (!apiKey) {
		console.log("[ANTHROPIC CHECK] ❌ Anthropic API key is not set");
		return { valid: false, status: "ANTHROPIC_API_KEY_NOT_SET" };
	}

	if (!isValidKeyFormat(apiKey)) {
		console.log(
			"[ANTHROPIC CHECK] ❌ Anthropic API key doesn't match the expected format"
		);
		return {
			valid: false,
			status: "ANTHROPIC_API_KEY_INVALID",
		};
	}

	const result = await validateApiKey(apiKey);
	return result;
}

function isValidKeyFormat(key: string): boolean {
	const regex = /^sk-ant-[a-zA-Z0-9_-]{32,}$/;
	return regex.test(key);
}

async function validateApiKey(apiKey: string): Promise<CheckStatus> {
	const response = await fetch("https://api.anthropic.com/v1/messages", {
		method: "POST",
		headers: {
			"x-api-key": apiKey,
			"anthropic-version": "2023-06-01",
			"content-type": "application/json",
		},
		body: JSON.stringify({
			model: "claude-3-haiku-20240307",
			max_tokens: 1,
			messages: [{ role: "user", content: "Hi" }],
		}),
	});

	if (response.status === 200) {
		console.log("[ANTHROPIC CHECK] ✅ API key is valid and has credit.");
		return { valid: true, status: "ANTHROPIC_VALID" };
	}

	if (response.status === 401) {
		console.log("[ANTHROPIC CHECK] ❌ Invalid API key.");
		return { valid: false, status: "ANTHROPIC_API_KEY_INVALID" };
	}

	const data = await response.json().catch(() => ({}));

	if (response.status === 403 && data.error?.message?.includes("billing")) {
		console.log(
			"[ANTHROPIC CHECK] ❌ API key has no credit or is not authorized."
		);
		return {
			valid: false,
			status: "ANTHROPIC_API_KEY_NO_CREDIT",
		};
	} else {
		console.log(`[ANTHROPIC CHECK] ⚠️ Unexpected error: ${data}`);
		return { valid: false, status: "ANTHROPIC_API_KEY_INVALID" };
	}
}
