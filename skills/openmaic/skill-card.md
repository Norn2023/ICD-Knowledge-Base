## Description:

OpenMAIC helps agents guide users through setting up, generating, and extending OpenMAIC multi-agent interactive classrooms, including Live Demo use, local setup, provider configuration, classroom generation, and SDK or product customization.

This skill is ready for commercial/non-commercial use.

## Publisher:

[wyuc](https://clawhub.ai/user/wyuc)

### License/Terms of Use:

MIT-0

## Use Case:

Developers, educators, and technical users use this skill to set up OpenMAIC, generate classroom experiences, configure provider credentials safely, and extend the OpenMAIC product or SDK.

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: Live Demo mode uses a stored access code for requests to open.maic.chat.

Mitigation: Store the access code in the local skill configuration, avoid pasting it into chat, and regenerate it if access fails or exposure is suspected.

Risk: Local mode may run dependency installs, dev servers, production builds, or Docker commands.

Mitigation: Confirm before each state-changing command, reuse an existing checkout only after reviewing its state, and verify the service health before generation.

Risk: SDK rendering can download fonts from file.maic.chat.

Mitigation: Account for this network dependency when operating offline or under restricted network policies, and review font handling when customizing renderer assets.

Risk: Provider keys and model selection are resolved by OpenMAIC server-side configuration.

Mitigation: Have users edit .env.local or server-providers.yml themselves, include explicit provider prefixes in DEFAULT_MODEL, and avoid request-time credential or model overrides.

## Reference(s):

- [OpenMAIC skill page](https://clawhub.ai/wyuc/skills/openmaic)
- [OpenMAIC Live Demo](https://open.maic.chat)
- [Clone Or Reuse Existing Repo](references/clone.md)
- [Startup Modes](references/startup-modes.md)
- [Provider Keys](references/provider-keys.md)
- [Generate Flow](references/generate-flow.md)
- [Live Demo Mode](references/live-demo.md)
- [Extend Or Build On OpenMAIC](references/extend.md)
- [Extend The OpenMAIC Product](references/extend-cookbook.md)
- [Consume The @openmaic/* SDK](references/extend-sdk.md)

## Skill Output:

**Output Type(s):** [Guidance, Markdown, Shell commands, Configuration, Code, API calls]

**Output Format:** [Markdown guidance with inline code, shell commands, configuration examples, and API request descriptions]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [The skill asks for confirmation before state-changing local actions and guides users to edit credentials in local configuration files rather than pasting keys into chat.]

## Skill Version(s):

0.3.3 (source: server release metadata)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment.
