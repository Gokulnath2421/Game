# data.py - The Scenario Database

SITUATIONS = {
    "Cricket": [
        {
            "scenario": "World Cup Final: 18 runs needed in 6 balls. A fast bouncer is coming at your head!",
            "options": ["A) Hook it for Six", "B) Duck/Leave it", "C) Upper-cut over third man"],
            "outcomes": {
                "A": {"success_msg": "CLEAN! It sails over the boundary! Momentum shifts!", "fail_msg": "Top edge! Caught at fine leg. The fans are devastated.", "chance": 40},
                "B": {"success_msg": "Good leave. It was a wide! 17 needed now.", "fail_msg": "It hit your helmet! You're dazed. -10 Fitness.", "chance": 85},
                "C": {"success_msg": "Perfectly timed! It flies for Four!", "fail_msg": "Thin edge to the Keeper. You're out!", "chance": 60}
            }
        },
        {
            "scenario": "A Bookie approaches you in a hotel lobby offering $100k to underperform.",
            "options": ["A) Report to Board", "B) Take the Cash", "C) Walk away"],
            "outcomes": {
                "A": {"success_msg": "Board is impressed! +20 Reputation, Grade Up!", "fail_msg": "No evidence found, media thinks you're lying.", "chance": 90},
                "B": {"success_msg": "The money is in your bank. Debt paid!", "fail_msg": "ANTI-CORRUPTION CAUGHT YOU! Lifetime Ban.", "chance": 30},
                "C": {"success_msg": "You kept your integrity.", "fail_msg": "The bookie leaks a fake photo of you meeting him!", "chance": 70}
            }
        }
    ],
    "Cinema": [
        {
            "scenario": "Press Meet: 'Your lead actress says you are difficult to work with. Is it true?'",
            "options": ["A) 'She's unprofessional'", "B) 'We just have different styles'", "C) 'No comment'"],
            "outcomes": {
                "A": {"success_msg": "The 'Tough Guy' image works. Fame +10", "fail_msg": "PR Disaster! Producers are scared of you.", "chance": 40},
                "B": {"success_msg": "Classy response. Reputation +15", "fail_msg": "People find you boring. Fame -5", "chance": 80},
                "C": {"success_msg": "The mystery grows.", "fail_msg": "Silence is taken as guilt. Boycott trend starts!", "chance": 60}
            }
        }
    ]
}