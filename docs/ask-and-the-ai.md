<sub>[Olam docs](README.md) › Learning the game</sub>

# Ask and the AI

Olam uses Claude for four things: answering rules questions, summing up a wiki page, running a solo adventure, and letting you interview the people in your world. They're optional. Everything else in Olam works without them, and the demo doesn't have them at all.

The one rule I held to is that the AI never makes things up from nowhere. Every answer is built from sources Olam found FIRST, and it cites them, so you can always check it. That matters a lot when you're learning, because a confident wrong answer about a rule is worse than no answer.

## Ask

**Ask** takes a rules question in plain words, like "How does grappling work?" or "Can I take a reaction on my own turn?", and answers it in two or three sentences, with a few bullet points if they help. There are a few example questions under the box to get you started.

Behind it, Olam searches its library first and hands Claude a numbered list of sources: the 2024 rules first, then the best expert answers from RPG Stack Exchange, and then passages from your own rulebooks if you've marked any. Claude answers from those sources only, cites them inline like [1] or [2][3], and says so plainly if they don't answer the question, instead of guessing. Under the answer is the list of sources, each with its badge, and each one opens its wiki page or thread.

When an expert answer is about the 2014 rules or another game, the answer says so. Answers are saved, so asking the same question again comes back straight away.

## Summarize

On a wiki page, **Summarize** writes two or three plain sentences about the entry for a new player or DM: what it is, and the one or two things that matter most at the table. It uses the rules text, the top expert answers and the myth roots, and cites them the same way. The summary is saved with the page, so you only wait for it once.

## The AI Game Master

Stop 4 on the Road, "A solo adventure with an AI GM", is a short adventure that Claude runs for you. You describe your character in a line, like "Tam, a halfling rogue who owes money to the wrong people", and press **Start the adventure**.

The Game Master sets the scene and asks what you do. When the outcome is uncertain, it asks for a specific roll, like "Roll a Dexterity (Stealth) check". You roll with the dice buttons right there in the app, add your modifier, and the total goes into your reply. It keeps the DC secret until after the roll, the way a real DM would. Whenever a rule comes up for the first time, the reply ends with a line that starts with **Rule:** and explains it in plain words.

The adventure takes about 15 exchanges and has one conversation, one bit of exploration and one small fight. The GM is told to be generous and never kill your character, because the point is to learn how it FEELS to play, not to lose. Your adventure is saved, so you can come back to it later, and **New adventure** starts over.

## Interviewing your characters

On a person's page in **People**, the **Interview** box lets you talk to them in character. They answer in their own voice, from their note in your vault: what they want, what they fear, who they know, and what they're hiding. They guard their secrets the way the character would, though a good question might make them slip.

This is how I get to know a character before I run them. When they make up a detail worth remembering, like a sister in the next town or where they were the night of the fire, it shows up under their reply with a **Keep** button. Press it and the detail goes into their note under **Details**, so it's part of your world from then on. Nothing goes into the note unless you keep it. [Map and People](map-and-people.md) has more about people.

## Connecting Claude

There are two ways, and Olam picks on its own:

- **An API key.** Put `ANTHROPIC_API_KEY=...` in `olam.env` (or in `.env` next to `compose.yaml` with Docker). If there's a key, Olam uses the Claude API.
- **Your Claude subscription.** If there's no key, Olam looks for the Claude CLI, signed in as the same user that runs Olam, and uses that. If it's somewhere unusual, set `OLAM_CLAUDE` to its path.

With neither, the AI features are off: Ask leaves the rail, Summarize and the Interview box don't show, and stop 4 says the Game Master is off. To turn them off on purpose, set `OLAM_AI=0`. The model is `claude-sonnet-5-5` by default, and `OLAM_MODEL` changes it. **Settings** shows which way Olam is connected and which model it's using.

## Next step

If you want to know where all those sources come from, and how far to trust each one, read [Where it all comes from](sources.md).

<sub>Next: [Where it all comes from](sources.md) →</sub>
