# Building a Home Assistant Integration with Claude Code: The Equation Virtus AC Story

## TL;DR

I reverse-engineered an undocumented AC API and built a complete Home Assistant integration in a single afternoon with Claude Code. Was it instant? No. Was it significantly faster than doing it alone? Absolutely.

## The Problem

I bought an Equation Virtus AC from Leroy Merlin. It works with their "Enki" app, but there's no Home Assistant integration. The existing `hacs-equation` repository only covers Equation radiators, which use a completely different Firebase-based API. My AC uses Adeo's cloud gateway with Keycloak OAuth2 - a totally different beast.

## The Approach

### Step 1: Capturing the API Traffic

Before Claude Code could help, I needed raw data. I set up mitmproxy on my machine and used `apk-mitm` to patch the Enki APK (bypassing SSL pinning). Then I used every feature in the app while capturing traffic.

This part was manual - Claude Code can't intercept my phone's network traffic. But once I had the `.mitm` flow files, that's where the collaboration began.

### Step 2: "Here's the API traffic, document it"

I pointed Claude Code at my mitmproxy captures and asked it to extract all the API details. It parsed through the HTTP flows and identified:

- The base URL (`https://enki.api.devportal.adeo.cloud`)
- Two different API keys for different services
- Keycloak OAuth2 authentication flow
- All the endpoints: state check, state change, error check, node info
- The complete JSON schema for requests and responses
- All enum values (modes, fan speeds, power states)

**Was it perfect on the first try?** Mostly. It correctly identified the main endpoints and data structures. One thing it initially missed was that `swingOrientation` in the POST request was `null` while the GET response showed `{"horizontal": "AUTO", "vertical": "AUTO"}`. I had to point that out from the raw captures.

### Step 3: "Create a git repo with documentation"

Claude Code created:
- A comprehensive README with full API documentation
- An example Python client demonstrating all operations
- Proper project structure

This was smooth - one prompt, complete output. The README included tables for enums, code examples, and even noted which API key to use for which service.

### Step 4: "Write a Home Assistant integration"

This is where things got interesting. Claude Code generated a complete integration:

- `manifest.json` with proper metadata
- `const.py` with all constants
- `api.py` with async HTTP client and token refresh
- `config_flow.py` with a multi-step setup wizard
- `coordinator.py` for polling and data updates
- `climate.py` for the main thermostat entity
- `strings.json` and translations

**Did it work immediately?** The structure was correct. The climate entity had all the right mappings. But when I asked "does this expose everything needed for automations?", I realized the special modes (quiet, sleep, health, frost protection, self-clean) were only exposed as read-only attributes.

### Step 5: The Back-and-Forth

Me: "Does the integration expose everything needed for automations?"

Claude Code: Listed what was available, noted that special modes were attributes only.

Me: "Yes we can [control them], if you check the mitm logs I can see: `{healthMode: true, quietMode: false...}`"

This was the key moment. Claude Code had made a reasonable assumption that boolean modes might be read-only (defrost actually is). But I had the ground truth from the API captures showing these modes were settable.

Claude Code then:
1. Created `switch.py` with 5 controllable switches
2. Created `binary_sensor.py` for defrost (the one truly read-only mode)
3. Created `sensor.py` for last reported timestamp
4. Updated `__init__.py` to register the new platforms
5. Updated the README with the new entities and automation examples

### Step 6: Documentation Review

Before pushing to GitHub, I asked Claude Code to ensure all documentation was up to date. It:
- Updated the README entities table
- Added example automations (quiet mode at night, turn off when leaving)
- Added helper methods to the example client
- Updated strings.json with all entity translations

### Step 7: Ship It

Created the GitHub repo, pushed everything. Done.

## The Verdict

### What Claude Code Did Well

1. **Structured extraction** - Parsing mitmproxy flows and identifying API patterns
2. **Boilerplate generation** - Home Assistant integrations have a LOT of boilerplate
3. **Consistency** - Keeping naming conventions, translations, and documentation in sync
4. **Iteration speed** - When I pointed out the missing switches, the fix was minutes not hours

### Where Human Input Was Essential

1. **Capturing the traffic** - No AI can intercept your phone's API calls
2. **Domain knowledge correction** - I knew from the raw API that modes were settable
3. **Prioritization** - Deciding what entities mattered for automations
4. **Verification** - Only I could test against the real device

### Time Estimate

| Task | Without Claude Code | With Claude Code |
|------|---------------------|------------------|
| API documentation | 2-3 hours | 20 minutes |
| Example client | 1 hour | 5 minutes |
| HA integration boilerplate | 3-4 hours | 30 minutes |
| Switch entities addition | 1-2 hours | 10 minutes |
| Documentation sync | 1 hour | 5 minutes |
| **Total** | **8-11 hours** | **~1.5 hours** |

The time savings aren't just about typing speed. It's about not having to:
- Look up Home Assistant's entity patterns for the 10th time
- Remember the exact structure of `manifest.json`
- Cross-reference translations between files
- Write repetitive dataclass definitions

## Lessons Learned

1. **Provide raw data, not summaries** - Claude Code works best when it can see the actual API responses, not my interpretation of them.

2. **Correct early, correct specifically** - When the modes were wrong, I showed the exact JSON proving they were settable. Specific corrections beat vague feedback.

3. **Trust but verify** - The generated code was structurally sound, but assumptions about API behavior needed human validation.

4. **Iterate in layers** - First the core climate entity, then switches, then sensors. Each layer was a chance to catch issues before adding complexity.

## The Result

A fully functional Home Assistant integration with:
- Climate entity (power, temperature, mode, fan, swing)
- 5 switch entities for special modes
- Binary sensor for defrost status
- Sensor for last update timestamp
- Multi-step config flow with device discovery
- Automatic token refresh
- Full API documentation

All published at: https://github.com/bcamarneiro/equation-virtus-ac-api

## Final Thoughts

Would I recommend Claude Code for this kind of project? Yes, with caveats:

- **Great for**: Boilerplate-heavy integrations, documentation, consistent code patterns
- **Still needs you for**: API discovery, testing, domain expertise, edge cases

It's not magic. It's a very capable collaborator that happens to never get tired of writing Home Assistant entity definitions. And honestly? That's exactly what I needed.

---

*Built with Claude Code. Tested with a very patient AC unit that's been turned on and off approximately 47 times today.*
