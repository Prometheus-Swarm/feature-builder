import { namespaceWrapper } from "@_koii/namespace-wrapper";
import { LogLevel } from "@_koii/namespace-wrapper/dist/types";
import { errorMessage, status } from "../../constants/checks";
import { checkAnthropic } from "./anthropicCheck";
import { checkGitHub } from "./githubCheck";
export async function preRunCheck(
	roundNumber: string,
	apiKey: string | undefined,
	username: string | undefined,
	token: string | undefined
) {
	const { valid: anthropicValid, status: anthropicStatus } =
		await checkAnthropic(apiKey);
	if (!anthropicValid) {
		await namespaceWrapper.logger(
			LogLevel.Error,
			errorMessage[anthropicStatus],
			anthropicStatus === "ANTHROPIC_API_KEY_NO_CREDIT"
				? "I understand"
				: "Set up credentials"
		);
		await namespaceWrapper.storeSet(
			`result-${roundNumber}`,
			status[anthropicStatus]
		);
		throw new Error(errorMessage[anthropicStatus]);
	}

	const { valid: githubValid, status: githubStatus } = await checkGitHub(
		username,
		token
	);

	if (!githubValid) {
		await namespaceWrapper.logger(
			LogLevel.Error,
			errorMessage[githubStatus],
			"Set up credentials"
		);
		await namespaceWrapper.storeSet(
			`result-${roundNumber}`,
			status[githubStatus]
		);
		throw new Error(errorMessage[githubStatus]);
	}
}
