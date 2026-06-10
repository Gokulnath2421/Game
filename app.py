from datetime import date, datetime, timedelta
import json
import os
import random

from flask import Flask, jsonify, redirect, render_template, request, url_for


app = Flask(__name__)
DATA_FILE = "game_data.json"
CURRENT_MATCH_PITCH = "Dust Bowl"

SCENE_LABELS = {
    "batting": "Batting Moment",
    "bowling": "Bowling Moment",
    "fielding": "Fielding Moment",
    "keeping": "Keeper Moment",
}

PLAYING_STYLES = {
    "Calm Finisher": {"confidence": 6, "stress": -4, "summary": "handles pressure and late-game choices well"},
    "Aggressive Opener": {"confidence": 8, "stress": 3, "summary": "starts fast and attracts attention quickly"},
    "Swing Specialist": {"confidence": 5, "stress": 0, "summary": "wins with movement and disciplined bowling plans"},
    "Mystery Spinner": {"confidence": 5, "stress": 1, "summary": "creates chances through deception and field traps"},
    "Safe Keeper": {"confidence": 4, "stress": -2, "summary": "builds trust through clean work behind the stumps"},
    "Pressure Fielder": {"confidence": 5, "stress": -1, "summary": "changes games with catches, stops, and direct hits"},
}

TRAINING_OPTIONS = {
    "nets": [
        {"id": "cover-drive", "label": "Cover Drive", "note": "Sharper batting timing", "confidence": 12, "stress": 8, "fitness": -1},
        {"id": "spin-reading", "label": "Read Spin", "note": "Better against turning pitches", "confidence": 10, "stress": 5, "fitness": 0},
        {"id": "yorker-control", "label": "Yorker Control", "note": "Death-over accuracy", "confidence": 9, "stress": 6, "fitness": -1},
    ],
    "gym": [
        {"id": "stamina", "label": "Stamina", "note": "Longer spells and better running", "confidence": 2, "stress": 5, "fitness": 12},
        {"id": "strength", "label": "Strength", "note": "More power under pressure", "confidence": 5, "stress": 6, "fitness": 9},
        {"id": "agility", "label": "Agility", "note": "Fielding and keeping boost", "confidence": 4, "stress": 4, "fitness": 10},
    ],
    "rest": [
        {"id": "sleep", "label": "Deep Sleep", "note": "Big stress recovery", "confidence": 1, "stress": -24, "fitness": 6},
        {"id": "physio", "label": "Physio", "note": "Protects against injuries", "confidence": 2, "stress": -12, "fitness": 12},
        {"id": "meditation", "label": "Meditation", "note": "Calmer decisions", "confidence": 6, "stress": -18, "fitness": 3},
    ],
}

RIVAL_NAMES = ["Arjun Mehta", "Kabir Rao", "Dev Nair"]
LEVELS = ["School", "District", "State", "National", "International"]


def choice(label, outcome, runs=0, wickets=0, confidence=0, stress=0, fitness=0, money=0, quality="good"):
    return {
        "label": label,
        "outcome": outcome,
        "effects": {
            "runs": runs,
            "wickets": wickets,
            "confidence": confidence,
            "stress": stress,
            "fitness": fitness,
            "money": money,
        },
        "quality": quality,
    }


SCENARIOS = {
    "batting": [
        {"id": "bat_01", "title": "New Ball Nibble", "prompt": "The ball is moving away outside off. What do you do?", "context": "Over 2.1 | Slip cordon waiting", "choices": [choice("Leave on length", "You judge it well and settle the nerves.", confidence=4, stress=-2), choice("Hard cover drive", "Thick edge flies past gully. Lucky runs, risky choice.", runs=4, stress=7, quality="risky"), choice("Soft hands to third", "Controlled single, scoreboard moving.", runs=1, confidence=2)]},
        {"id": "bat_02", "title": "Spinner Tosses It Up", "prompt": "A loopy off-break invites the big shot.", "context": "Over 8.4 | Long-on is back", "choices": [choice("Work with the spin", "Smart wrists find a calm single.", runs=1, confidence=3), choice("Charge and loft", "Clean strike over long-on.", runs=6, confidence=6, stress=5, quality="risky"), choice("Pad it away", "The umpire ignores the shout, but pressure builds.", stress=4, quality="bad")]},
        {"id": "bat_03", "title": "Short Ball Trap", "prompt": "The bowler bangs it in with fine leg deep.", "context": "Over 5.2 | Two men behind square", "choices": [choice("Roll the pull down", "Kept along the carpet for two.", runs=2, confidence=4), choice("Hook in the air", "Top edge lands safe. Not convincing.", runs=1, stress=6, quality="risky"), choice("Duck under it", "Good awareness. No damage.", confidence=2, stress=-1)]},
        {"id": "bat_04", "title": "Death Over Yorker", "prompt": "Full and fast at the base of off stump.", "context": "Over 18.5 | Boundary needed", "choices": [choice("Open face late", "Brilliant adjustment, four behind point.", runs=4, confidence=7), choice("Wild slog", "You miss and nearly lose off stump.", stress=8, quality="bad"), choice("Dig it out", "Safe single under pressure.", runs=1, confidence=2)]},
        {"id": "bat_05", "title": "Singles Choke", "prompt": "The field is spread and the non-striker wants quick runs.", "context": "Middle overs | Required rate rising", "choices": [choice("Drop and run", "Sharp call, easy single.", runs=1, confidence=3), choice("Refuse the run", "Partner is stranded halfway but recovers.", stress=6, quality="bad"), choice("Sweep hard", "Beats square leg for four.", runs=4, confidence=4, quality="risky")]},
        {"id": "bat_06", "title": "Left-Arm Angle", "prompt": "A left-armer angles across from over the wicket.", "context": "Over 3.3 | Ball still swinging", "choices": [choice("Play under the eyes", "Compact defence earns applause.", confidence=4, stress=-2), choice("Reach outside off", "Beaten by the angle.", stress=5, quality="bad"), choice("Clip straight", "Timed well for two.", runs=2, confidence=3)]},
        {"id": "bat_07", "title": "Free Hit", "prompt": "No-ball called. You cannot be bowled out.", "context": "Over 11.1 | Free hit", "choices": [choice("Clear front leg", "Hammered over midwicket.", runs=6, confidence=8), choice("Take a safe single", "Useful, but you left runs out there.", runs=1, confidence=1), choice("Reverse sweep", "Missed completely.", stress=4, quality="bad")]},
        {"id": "bat_08", "title": "Part-Time Bowler", "prompt": "A nervous part-timer floats one too full.", "context": "Over 13.2 | Captain searching", "choices": [choice("Straight drive", "Pure timing down the ground.", runs=4, confidence=6), choice("Overhit to leg", "Mistimed for one.", runs=1, stress=2), choice("Block it", "You let the bowler escape.", stress=3, quality="bad")]},
        {"id": "bat_09", "title": "Hat-Trick Ball", "prompt": "Crowd is loud, fielders crowd the bat.", "context": "Over 9.6 | Hat-trick ball", "choices": [choice("Dead bat", "Stonewall defence. Pressure handled.", confidence=5, stress=-4), choice("Counterattack", "Bold drive splits cover.", runs=4, confidence=7, stress=4, quality="risky"), choice("Nervous poke", "Inside edge saves you.", stress=7, quality="bad")]},
        {"id": "bat_10", "title": "Runner Struggling", "prompt": "Your partner is tired and slow between wickets.", "context": "Over 15.3 | Partnership building", "choices": [choice("Call only clear runs", "Mature game sense keeps control.", confidence=4), choice("Push risky two", "Run-out chance missed.", runs=2, stress=8, quality="risky"), choice("Farm strike", "You keep the strike with a late single.", runs=1, confidence=3)]},
        {"id": "bat_11", "title": "Leg Spinner's Wrong One", "prompt": "You suspect the wrong one is coming.", "context": "Over 10.2 | Slip in place", "choices": [choice("Read from the hand", "Picked early and punched for two.", runs=2, confidence=5), choice("Pre-meditate sweep", "It turns the other way and beats you.", stress=6, quality="bad"), choice("Use the crease", "Late adjustment, safe defence.", confidence=3)]},
        {"id": "bat_12", "title": "Powerplay Gap", "prompt": "Mid-off is inside the circle.", "context": "Over 4.5 | Hard new ball", "choices": [choice("Loft over mid-off", "Clean elevation, four runs.", runs=4, confidence=5), choice("Punch to cover", "Straight to the fielder.", stress=2), choice("Tap to point", "Quick single stolen.", runs=1, confidence=2)]},
        {"id": "bat_13", "title": "Slow Bouncer", "prompt": "The bowler rolls fingers over a short ball.", "context": "Over 16.1 | Pace off", "choices": [choice("Wait and ramp", "Excellent touch over keeper.", runs=4, confidence=6), choice("Early pull", "Through the shot too soon.", stress=5, quality="bad"), choice("Let it pass", "Dot ball, but safe.", stress=1)]},
        {"id": "bat_14", "title": "Chase Equation", "prompt": "Eight needed from the final over. First ball is on the pads.", "context": "Over 19.1 | Chase pressure", "choices": [choice("Clip for two", "Smart start to the over.", runs=2, confidence=4), choice("Huge leg-side slog", "Skied but dropped.", runs=1, stress=8, quality="risky"), choice("Defend", "Dot ball hurts the chase.", stress=6, quality="bad")]},
        {"id": "bat_15", "title": "Milestone Nerves", "prompt": "You are close to a fifty and the field comes up.", "context": "Personal milestone", "choices": [choice("Stay busy", "Single taken. Milestone pressure eases.", runs=1, confidence=5), choice("Force boundary", "Mistimed but safe.", runs=1, stress=5, quality="risky"), choice("Freeze up", "Dot ball. The moment grows.", stress=4, quality="bad")]},
    ],
    "bowling": [
        {"id": "bowl_01", "title": "New Batter Arrives", "prompt": "Fresh batter is marking guard. What is your plan?", "context": "Over 6.1 | One slip waiting", "choices": [choice("Attack off stump", "Perfect channel, batter plays and misses.", confidence=5), choice("Bouncer first ball", "Too high. Umpire warns you.", stress=5, quality="bad"), choice("Full slower ball", "Deceived and chipped to cover.", wickets=1, confidence=8)]},
        {"id": "bowl_02", "title": "Set Batter Charging", "prompt": "The batter is stepping out before release.", "context": "Over 12.4 | Spinner under pressure", "choices": [choice("Pull length back", "Beats the charge and keeper gathers.", confidence=5), choice("Fire it wider", "Stumping chance created.", wickets=1, confidence=8), choice("Toss it higher", "Launched over long-on.", stress=8, quality="bad")]},
        {"id": "bowl_03", "title": "Death Over Plan", "prompt": "Six balls left, twelve to defend.", "context": "Final over", "choices": [choice("Wide yorker", "Nails the tramline. Dot ball.", confidence=6), choice("Length ball", "Disappears over midwicket.", stress=8, quality="bad"), choice("Slower bouncer", "Mistimed to deep square.", wickets=1, confidence=7)]},
        {"id": "bowl_04", "title": "Left-Hand Matchup", "prompt": "A left-hander is targeting the short boundary.", "context": "Over 9.3 | Wind across ground", "choices": [choice("Around the wicket", "Angle cramps the batter.", confidence=4), choice("Overpitch outside off", "Driven hard for four.", stress=6, quality="bad"), choice("Body-line field", "Single only, plan works.", confidence=3)]},
        {"id": "bowl_05", "title": "Wet Ball", "prompt": "Dew makes the ball hard to grip.", "context": "Night match", "choices": [choice("Cross-seam length", "Skids through safely.", confidence=4), choice("Try big leg cutter", "Slips out as a full toss.", stress=7, quality="bad"), choice("Ask towel and reset", "Calm reset improves control.", stress=-3, confidence=3)]},
        {"id": "bowl_06", "title": "Tailender On Strike", "prompt": "Tailender backs away early.", "context": "Over 17.2 | Fielders close", "choices": [choice("Fast at the stumps", "Middle stump flattened.", wickets=1, confidence=8), choice("Short and wide", "Slashed over point.", stress=6, quality="bad"), choice("Slower yorker", "Dug out for a single.", confidence=2)]},
        {"id": "bowl_07", "title": "Powerplay Attack", "prompt": "Two slips are in, ball is swinging.", "context": "Over 1.5", "choices": [choice("Pitch it up", "Edge flies to slip.", wickets=1, confidence=8), choice("Back of length", "Safe dot, but less threat.", confidence=2), choice("Bowl on pads", "Clipped away for runs.", stress=5, quality="bad")]},
        {"id": "bowl_08", "title": "Batter Sweeping", "prompt": "The batter has swept you twice.", "context": "Spin spell", "choices": [choice("Move square leg back", "Sweep is cut to one.", confidence=3), choice("Quicker at pads", "Trapped in front.", wickets=1, confidence=8), choice("Same loop again", "Swept hard for four.", stress=6, quality="bad")]},
        {"id": "bowl_09", "title": "Short Boundary", "prompt": "One side of the ground is tiny.", "context": "Captain asks for a plan", "choices": [choice("Bowl to long side", "Batter forced into low-value shot.", confidence=4), choice("Ignore field", "Pulled into the short side.", stress=7, quality="bad"), choice("Change pace wide", "Mistimed for one.", confidence=3)]},
        {"id": "bowl_10", "title": "Hat-Trick Chance", "prompt": "Two wickets in two balls. Crowd rises.", "context": "Hat-trick ball", "choices": [choice("Best stock ball", "Beats the edge by inches.", confidence=6), choice("Too clever slower ball", "Picked early and hit.", stress=6, quality="bad"), choice("Yorker at off stump", "Toe-crusher. Huge appeal denied.", confidence=5)]},
        {"id": "bowl_11", "title": "Captain Wants Aggression", "prompt": "Captain asks for a wicket, but the batter is set.", "context": "Middle overs", "choices": [choice("Set trap at deep midwicket", "Batter holes out to the plan.", wickets=1, confidence=8), choice("Bowl miracle ball", "Loses line completely.", stress=7, quality="bad"), choice("Build dots first", "Pressure returns.", confidence=4)]},
        {"id": "bowl_12", "title": "No-Ball Fear", "prompt": "You overstepped last ball.", "context": "Free hit survived", "choices": [choice("Shorten run-up", "Control returns instantly.", confidence=4, stress=-2), choice("Think about crease", "Distracted and too full.", stress=5, quality="bad"), choice("Trust normal rhythm", "Good pace, safe length.", confidence=3)]},
        {"id": "bowl_13", "title": "Reverse Swing Hint", "prompt": "One side of the ball is shining nicely.", "context": "Old ball", "choices": [choice("Attack base of off", "Late tail, stumps everywhere.", wickets=1, confidence=9), choice("Bowl short", "Wastes the reverse swing.", stress=3, quality="bad"), choice("Set leg slip", "Inside edge nearly carries.", confidence=5)]},
        {"id": "bowl_14", "title": "Batter Walks Across", "prompt": "The batter shuffles outside off to scoop.", "context": "Death overs", "choices": [choice("Follow with yorker", "Pins the toes. Dot ball.", confidence=5), choice("Slower ball into pitch", "Top edge caught fine.", wickets=1, confidence=8), choice("Predictable wide ball", "Ramp shot beats short third.", stress=7, quality="bad")]},
        {"id": "bowl_15", "title": "Long Spell Fatigue", "prompt": "Your legs are heavy late in the spell.", "context": "Fourth over", "choices": [choice("Simplify line", "Accurate dot ball.", confidence=4, fitness=-1), choice("Force extra pace", "Strain rises and line suffers.", stress=6, fitness=-4, quality="bad"), choice("Use slower cutter", "Mistimed to cover.", confidence=4)]},
    ],
    "fielding": [
        {"id": "field_01", "title": "Hard Chance at Point", "prompt": "A cut shot flies fast to your right.", "context": "Point position", "choices": [choice("Dive both hands", "Brilliant stop saves four.", confidence=6, fitness=-1), choice("Stay back", "Ball races away.", stress=5, quality="bad"), choice("Half dive", "You save two but miss the chance.", confidence=1)]},
        {"id": "field_02", "title": "Boundary Relay", "prompt": "The ball slows near the rope.", "context": "Deep cover", "choices": [choice("Slide and relay", "Clean save, only two.", confidence=5, fitness=-1), choice("Pick up one-handed", "Fumble gives extra run.", stress=5, quality="bad"), choice("Let partner chase", "Safe but slow.", stress=2)]},
        {"id": "field_03", "title": "Run-Out Chance", "prompt": "Batter turns for a risky second.", "context": "Deep square leg", "choices": [choice("Throw to keeper", "Direct line creates run-out.", wickets=1, confidence=8), choice("Throw to bowler", "Wrong end, chance gone.", stress=5, quality="bad"), choice("Hold the ball", "No overthrow, but no wicket.", confidence=1)]},
        {"id": "field_04", "title": "Skier in the Sun", "prompt": "The ball hangs high and the sun is in your eyes.", "context": "Mid-off", "choices": [choice("Use hands as shade", "Safe catch under pressure.", wickets=1, confidence=8), choice("Backpedal late", "Dropped catch.", stress=8, quality="bad"), choice("Call early", "Teammate takes it cleanly.", confidence=4)]},
        {"id": "field_05", "title": "Close-In Reflex", "prompt": "A firm push comes straight at silly point.", "context": "Close catcher", "choices": [choice("Stay low", "Sharp reflex stop.", confidence=6), choice("Turn away", "Captain is not pleased.", stress=5, quality="bad"), choice("Parry upward", "Almost a catch.", confidence=2, stress=2)]},
        {"id": "field_06", "title": "Misfield Recovery", "prompt": "You bobble the pickup and the batter runs.", "context": "Cover ring", "choices": [choice("Recover and throw", "You limit it to one.", confidence=2), choice("Panic throw", "Overthrow costs another run.", stress=7, quality="bad"), choice("Hold and reset", "Safe, but pressure remains.", stress=2)]},
        {"id": "field_07", "title": "Captain Moves You", "prompt": "Captain asks you to guard a hot zone.", "context": "Tactical field change", "choices": [choice("Ask exact angle", "Perfect position saves runs.", confidence=5), choice("Guess the spot", "Ball beats you by a yard.", stress=4, quality="bad"), choice("Stand deeper", "Single saved, boundary protected.", confidence=2)]},
        {"id": "field_08", "title": "Crowd Noise", "prompt": "You cannot hear the keeper's call.", "context": "Ring field", "choices": [choice("Use visual signal", "Clean coordination.", confidence=4), choice("Both chase", "Collision nearly happens.", stress=6, quality="bad"), choice("Leave loudly", "Safe communication.", confidence=3)]},
        {"id": "field_09", "title": "Wet Outfield", "prompt": "The turf is slippery after rain.", "context": "Long-on", "choices": [choice("Controlled slide", "Textbook boundary save.", confidence=5, fitness=-1), choice("Sprint full tilt", "You slip and lose balance.", stress=6, fitness=-2, quality="bad"), choice("Stay on feet", "Concedes two safely.", confidence=1)]},
        {"id": "field_10", "title": "Pressure Catch", "prompt": "Set batter picks you out at deep midwicket.", "context": "Crowd holding breath", "choices": [choice("Settle under it", "Massive catch taken.", wickets=1, confidence=9), choice("Run in too far", "Ball sails over you.", stress=8, quality="bad"), choice("Take it chest-high", "Safe catch, good hands.", wickets=1, confidence=7)]},
        {"id": "field_11", "title": "Backing Up", "prompt": "A throw is coming at the bowler's end.", "context": "Mid-on", "choices": [choice("Back up behind stumps", "Saves overthrows.", confidence=4), choice("Watch the ball", "No backup, extra run.", stress=5, quality="bad"), choice("Shout instructions", "Helps the bowler gather.", confidence=2)]},
        {"id": "field_12", "title": "Quick Single", "prompt": "Batter drops it near you and calls instantly.", "context": "Short cover", "choices": [choice("Attack the ball", "Run-out pressure, dot ball.", confidence=5), choice("Wait for bounce", "Easy single conceded.", stress=3, quality="bad"), choice("Underarm flick", "Close miss at stumps.", confidence=3)]},
        {"id": "field_13", "title": "Boundary Judgement", "prompt": "A lofted shot is dropping near the rope.", "context": "Long-off", "choices": [choice("Catch inside, release before rope", "Spectacular relay catch.", wickets=1, confidence=10, fitness=-1), choice("Step on rope", "Six signalled.", stress=8, quality="bad"), choice("Save boundary first", "Keeps it to two.", confidence=3)]},
        {"id": "field_14", "title": "Ball Lost in Lights", "prompt": "The white ball disappears under floodlights.", "context": "Deep point", "choices": [choice("Track from batter's swing", "You recover the line.", confidence=5), choice("Freeze", "Ball lands beside you.", stress=6, quality="bad"), choice("Call for help", "Teammate covers ground.", confidence=2)]},
        {"id": "field_15", "title": "Injury Scare", "prompt": "Your ankle twists slightly during a chase.", "context": "Outfield", "choices": [choice("Signal physio", "Short delay keeps you fit.", fitness=2, stress=-2), choice("Hide it", "You worsen the niggle.", fitness=-7, stress=4, quality="bad"), choice("Move to safer position", "Captain accepts the call.", fitness=1, confidence=2)]},
    ],
    "keeping": [
        {"id": "keep_01", "title": "Standing Up", "prompt": "Medium pacer asks you to stand up to the stumps.", "context": "Batter leaving crease", "choices": [choice("Stand up with helmet", "Pressure creates a stumping chance.", wickets=1, confidence=8), choice("Stay back", "Batter keeps charging freely.", stress=4, quality="bad"), choice("Stand halfway", "Awkward but safe.", confidence=1)]},
        {"id": "keep_02", "title": "Thick Edge", "prompt": "Edge flies low between you and first slip.", "context": "New ball", "choices": [choice("Go with both gloves", "Clean catch inches above turf.", wickets=1, confidence=9), choice("Leave to slip", "It drops short.", stress=5, quality="bad"), choice("Deflect safely", "You save runs but miss catch.", confidence=2)]},
        {"id": "keep_03", "title": "Leg-Side Take", "prompt": "Ball sprays down leg and batter overbalances.", "context": "Spinner operating", "choices": [choice("Collect and whip bails", "Lightning stumping.", wickets=1, confidence=9), choice("Appeal first", "Chance disappears.", stress=6, quality="bad"), choice("Block with pads", "No bye conceded.", confidence=3)]},
        {"id": "keep_04", "title": "DRS Call", "prompt": "Bowler screams LBW. You had the best view.", "context": "Big appeal", "choices": [choice("Advise no review", "Impact was outside. Review saved.", confidence=5), choice("Burn the review", "Replay proves you wrong.", stress=7, quality="bad"), choice("Ask bowler what he saw", "Calm discussion helps.", confidence=3)]},
        {"id": "keep_05", "title": "Bye Prevention", "prompt": "A rough pitch sends one exploding past off stump.", "context": "Uneven bounce", "choices": [choice("Stay soft with gloves", "Brilliant take, no bye.", confidence=6), choice("Snatch at it", "Ball bursts through.", stress=5, quality="bad"), choice("Use body behind gloves", "Safe block.", confidence=3)]},
        {"id": "keep_06", "title": "Keeper Sledging", "prompt": "Batter looks rattled after two plays and misses.", "context": "Pressure moment", "choices": [choice("Encourage bowler", "Team energy rises.", confidence=4), choice("Overdo the chatter", "Umpire warns you.", stress=5, quality="bad"), choice("Stay silent and focused", "You remain sharp.", confidence=3)]},
        {"id": "keep_07", "title": "Inside Edge", "prompt": "Inside edge ricochets onto pad and loops up.", "context": "Close chance", "choices": [choice("Dive forward", "Outstanding reflex catch.", wickets=1, confidence=9), choice("Wait flat-footed", "Ball dies short.", stress=5, quality="bad"), choice("Call keeper's catch", "You commit early and gather.", wickets=1, confidence=7)]},
        {"id": "keep_08", "title": "Field Adjustment", "prompt": "You spot the batter opening the face repeatedly.", "context": "Third-man gap", "choices": [choice("Move slip wider", "Edge goes straight to him.", wickets=1, confidence=8), choice("Say nothing", "Another boundary leaks.", stress=6, quality="bad"), choice("Bring point finer", "Single line is closed.", confidence=4)]},
        {"id": "keep_09", "title": "Stumping Review", "prompt": "Bails are off. Foot may be on the line.", "context": "TV umpire moment", "choices": [choice("Stay calm", "Replay shows foot lifted. Out.", wickets=1, confidence=7), choice("Celebrate early", "Not out, you look rattled.", stress=5, quality="bad"), choice("Check with square leg", "Professional process.", confidence=3)]},
        {"id": "keep_10", "title": "Low Bounce", "prompt": "Spinner bowls one that barely carries.", "context": "Dusty pitch", "choices": [choice("Sink lower early", "Clean take from the floor.", confidence=6), choice("Rise too soon", "Bye conceded.", stress=5, quality="bad"), choice("Body stop", "Messy but effective.", confidence=3)]},
        {"id": "keep_11", "title": "Run-Out at Striker End", "prompt": "Throw arrives wide with batter short.", "context": "Keeper's end", "choices": [choice("Sweep into stumps", "Fast hands complete run-out.", wickets=1, confidence=9), choice("Catch then turn", "Too slow.", stress=5, quality="bad"), choice("Kick toward stumps", "Creative, but misses.", stress=3, quality="risky")]},
        {"id": "keep_12", "title": "Bowler Losing Line", "prompt": "Your bowler is spraying wides.", "context": "Pressure spell", "choices": [choice("Walk up and reset him", "Next ball lands perfectly.", confidence=5), choice("Show frustration", "Bowler gets worse.", stress=6, quality="bad"), choice("Set bigger leg-side target", "Wides reduce.", confidence=3)]},
        {"id": "keep_13", "title": "Standing Back Edge", "prompt": "Fast bowler finds a faint outside edge.", "context": "Over 4.2", "choices": [choice("Stay still until edge", "Clean catch at chest height.", wickets=1, confidence=8), choice("Move early leg side", "Wrong-footed drop.", stress=7, quality="bad"), choice("Dive after movement", "Good save, no catch.", confidence=2)]},
        {"id": "keep_14", "title": "Final Over Calm", "prompt": "Everyone is shouting field changes.", "context": "Final over", "choices": [choice("Give one clear message", "Bowler executes the plan.", confidence=5), choice("Join the noise", "Confusion costs a run.", stress=5, quality="bad"), choice("Check field quietly", "No gaps left open.", confidence=4)]},
        {"id": "keep_15", "title": "Keeper Batting Tail", "prompt": "You come in at seven with wickets falling.", "context": "Lower middle order", "choices": [choice("Stabilize first", "Useful partnership begins.", runs=2, confidence=5), choice("Swing first ball", "Top edge lands safe.", runs=1, stress=6, quality="risky"), choice("Farm strike calmly", "You guide the tail.", runs=4, confidence=6)]},
    ],
}


def today_string():
    return date.today().strftime("%Y-%m-%d")


def calculate_age(date_of_birth, current_date):
    try:
        dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        current = datetime.strptime(current_date, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return 15

    age = current.year - dob.year
    if (current.month, current.day) < (dob.month, dob.day):
        age -= 1
    return max(0, age)


def advance_player_day(p):
    d_obj = datetime.strptime(p["current_date"], "%Y-%m-%d")
    p["current_date"] = (d_obj + timedelta(days=1)).strftime("%Y-%m-%d")
    if p.get("date_of_birth"):
        p["age"] = calculate_age(p["date_of_birth"], p["current_date"])
    return p


def build_calendar_days(current_date):
    current = datetime.strptime(current_date, "%Y-%m-%d")
    days = []
    for offset in range(-2, 3):
        day = current + timedelta(days=offset)
        days.append({
            "number": day.strftime("%d"),
            "label": "Today" if offset == 0 else day.strftime("%b"),
            "is_current": offset == 0,
            "is_match": day.day % 6 == 0,
        })
    return days


def select_match_scenarios(role):
    plans = {
        "Batsman": ["batting", "fielding", "batting"],
        "Bowler": ["bowling", "fielding", random.choice(["bowling", "batting"])],
        "All-Rounder": ["batting", "bowling", "fielding"],
        "Wicket-Keeper": ["keeping", random.choice(["batting", "keeping"]), "fielding"],
    }
    scene_plan = plans.get(role, ["fielding", "batting", "fielding"])
    question_count = random.choice([2, 3])
    selected = []

    for scene in scene_plan[:question_count]:
        pool = [s for s in SCENARIOS[scene] if s["id"] not in {item["id"] for item in selected}]
        scenario = random.choice(pool)
        selected.append({
            "scene": scene,
            "id": scenario["id"],
            "title": scenario["title"],
            "prompt": scenario["prompt"],
            "context": scenario["context"],
            "choices": scenario["choices"],
        })

    return selected


def apply_choice_effects(p, effects):
    stats = p.setdefault("stats", {})
    stats["runs"] = stats.get("runs", 0) + effects.get("runs", 0)
    stats["wickets"] = stats.get("wickets", 0) + effects.get("wickets", 0)
    p["confidence"] = max(0, min(100, p.get("confidence", 0) + effects.get("confidence", 0)))
    p["stress"] = max(0, min(100, p.get("stress", 0) + effects.get("stress", 0)))
    p["fitness"] = max(0, min(100, p.get("fitness", 0) + effects.get("fitness", 0)))
    p["money"] = max(0, p.get("money", 0) + effects.get("money", 0))


def add_memory(p, text):
    memories = p.setdefault("memories", [])
    if text not in memories:
        memories.insert(0, text)
    p["memories"] = memories[:8]


def ensure_career_systems(p):
    p.setdefault("playing_style", "Calm Finisher")
    p.setdefault("form", 50)
    p.setdefault("fans", 10)
    p.setdefault("selection_status", "Local Prospect")
    p.setdefault("coach_note", "Coach wants to see consistency over the next few match days.")
    p.setdefault("headline", "Local youngster begins the long road.")
    p.setdefault("sponsor", {"name": "No sponsor yet", "deal": 0, "pressure": 0})
    p.setdefault("relationships", {"Coach": 50, "Captain": 50, "Fans": 10, "Selectors": 35})
    p.setdefault("injury", {"status": "Fit", "days": 0})
    p.setdefault("memories", [])
    if "rivals" not in p:
        p["rivals"] = [{"name": name, "form": random.randint(42, 64), "level": p.get("level", "School")} for name in RIVAL_NAMES]
    if "training_log" not in p:
        p["training_log"] = []
    return p


def clamp_career_values(p):
    for key in ["form", "fans"]:
        p[key] = max(0, min(100, p.get(key, 0)))
    for key, value in p["relationships"].items():
        p["relationships"][key] = max(0, min(100, value))


def update_rivals(p, impact_score):
    for rival in p["rivals"]:
        rival["form"] = max(0, min(100, rival["form"] + random.randint(-3, 7)))
        if rival["form"] > p["form"] + 18 and random.random() < 0.25:
            rival["level"] = LEVELS[min(LEVELS.index(rival["level"]) + 1, len(LEVELS) - 1)] if rival["level"] in LEVELS else rival["level"]
    if p["rivals"]:
        top = max(p["rivals"], key=lambda r: r["form"])
        if top["form"] > p["form"]:
            return f"{top['name']} is putting pressure on your selection spot with a form rating of {top['form']}."
    return "Your rivals noticed the performance."


def update_selection(p, impact_score):
    matches = p["stats"].get("matches", 0)
    if impact_score >= 4:
        p["form"] += 10
        p["relationships"]["Selectors"] += 7
        p["relationships"]["Coach"] += 5
    elif impact_score >= 1:
        p["form"] += 4
        p["relationships"]["Captain"] += 3
    else:
        p["form"] -= 6
        p["relationships"]["Selectors"] -= 4
        p["relationships"]["Coach"] -= 3

    current_level = p.get("level", "School")
    level_index = LEVELS.index(current_level) if current_level in LEVELS else 0
    if matches and matches % 4 == 0 and p["form"] >= 70 and p["relationships"]["Selectors"] >= 55 and level_index < len(LEVELS) - 1:
        p["level"] = LEVELS[level_index + 1]
        p["selection_status"] = f"Promoted to {p['level']} squad"
        add_memory(p, f"Earned promotion to the {p['level']} squad.")
    elif p["form"] < 30:
        p["selection_status"] = "Under selection pressure"
    elif p["form"] >= 60:
        p["selection_status"] = "In selection conversation"
    else:
        p["selection_status"] = "Local Prospect"


def update_sponsor(p):
    fame = p["fans"] + p["stats"].get("matches", 0) * 3 + (15 if p.get("level") in ["State", "National", "International"] else 0)
    if fame >= 95:
        p["sponsor"] = {"name": "Apex Cricket Gear", "deal": 2500, "pressure": 12}
    elif fame >= 65:
        p["sponsor"] = {"name": "Metro Sports", "deal": 1200, "pressure": 7}
    elif fame >= 40:
        p["sponsor"] = {"name": "Local Bat Co.", "deal": 500, "pressure": 3}


def update_injury(p):
    injury = p.setdefault("injury", {"status": "Fit", "days": 0})
    if injury["days"] > 0:
        injury["days"] -= 1
        if injury["days"] == 0:
            injury["status"] = "Fit"
            add_memory(p, "Returned to full fitness after an injury scare.")
    risk = max(0, p["stress"] - 70) + max(0, 45 - p["fitness"])
    if injury["status"] == "Fit" and random.randint(1, 100) <= min(30, risk):
        injury["status"] = "Minor niggle"
        injury["days"] = random.randint(2, 4)
        p["fitness"] = max(0, p["fitness"] - 8)
        p["coach_note"] = "Medical team wants reduced workload for a few days."
        add_memory(p, "Picked up a minor niggle after pushing through fatigue.")


def build_headline(p, match, impact_score):
    if impact_score >= 4:
        return f"{p['name']} makes smart calls as {p['level']} stock rises."
    if match["wickets"] > 0:
        return f"{p['name']} changes the game with a key wicket involvement."
    if match["runs"] >= 6:
        return f"{p['name']} adds useful runs in a tense passage."
    return f"Selectors ask for sharper decisions from {p['name']}."


def update_milestones(p, match):
    stats = p["stats"]
    if stats.get("matches", 0) == 1:
        add_memory(p, "Made career debut.")
    if stats.get("runs", 0) >= 50:
        add_memory(p, "Crossed 50 career runs.")
    if stats.get("wickets", 0) >= 5:
        add_memory(p, "Reached 5 career wicket involvements.")
    if match["runs"] >= 6:
        add_memory(p, "Produced a decisive batting moment.")
    if match["wickets"] >= 1:
        add_memory(p, "Created a wicket in a pressure moment.")


def apply_post_match_story(p, match, impact_score):
    p["fans"] += 8 if impact_score >= 4 else 4 if impact_score >= 1 else -2
    p["money"] += p.get("sponsor", {}).get("deal", 0)
    p["headline"] = build_headline(p, match, impact_score)
    p["coach_note"] = "Coach praised your decision-making." if impact_score >= 4 else "Coach wants the same clarity next match." if impact_score >= 1 else "Coach flagged decision pressure as a work-on."
    rival_note = update_rivals(p, impact_score)
    update_selection(p, impact_score)
    update_sponsor(p)
    update_injury(p)
    update_milestones(p, match)
    clamp_career_values(p)
    match["headline"] = p["headline"]
    match["coach_note"] = p["coach_note"]
    match["rival_note"] = rival_note
    match["selection_status"] = p["selection_status"]
    match["sponsor"] = p["sponsor"]
    match["injury"] = p["injury"]


def load_data():
    if not os.path.exists(DATA_FILE):
        return None

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    if "stats" not in data:
        data["stats"] = {"runs": 0, "matches": 0, "wickets": 0, "centuries": 0}
    if "wickets" not in data["stats"]:
        data["stats"]["wickets"] = 0
    if "centuries" not in data["stats"]:
        data["stats"]["centuries"] = 0
    if data.get("date_of_birth"):
        data["age"] = calculate_age(data["date_of_birth"], data.get("current_date", today_string()))
    ensure_career_systems(data)

    return data


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


@app.route("/")
def landing():
    p = load_data()
    return render_template("landing.html", p=p, today=today_string())


@app.route("/new_game", methods=["POST"])
def new_game():
    username = request.form.get("username", "Player")
    role = request.form.get("role", "Batsman")
    playing_style = request.form.get("playing_style", "Calm Finisher")
    date_of_birth = request.form.get("date_of_birth", "")
    current_date = date_of_birth or today_string()
    age = calculate_age(date_of_birth, current_date)
    style_boost = PLAYING_STYLES.get(playing_style, PLAYING_STYLES["Calm Finisher"])
    new_p = {
        "name": username,
        "role": role,
        "playing_style": playing_style,
        "level": "School",
        "age": age,
        "date_of_birth": date_of_birth,
        "tournament": "Inter-School Cup",
        "format": "T20",
        "money": 500,
        "stress": max(0, 10 + style_boost["stress"]),
        "fitness": 90,
        "confidence": min(100, 50 + style_boost["confidence"]),
        "current_date": current_date,
        "start_date": current_date,
        "stats": {"runs": 0, "matches": 0, "centuries": 0, "motm": 0, "wickets": 0},
        "season_scores": [],
        "points_table": [
            {"team": "Your Team", "p": 0, "w": 0, "l": 0, "pts": 0},
            {"team": "Titans", "p": 0, "w": 0, "l": 0, "pts": 0},
            {"team": "Strikers", "p": 0, "w": 0, "l": 0, "pts": 0},
            {"team": "Warriors", "p": 0, "w": 0, "l": 0, "pts": 0},
        ],
    }
    ensure_career_systems(new_p)
    add_memory(new_p, f"Started career as a {playing_style} {role}.")
    save_data(new_p)
    return redirect(url_for("game"))


@app.route("/game")
def game():
    p = load_data()
    if not p:
        return redirect(url_for("landing"))

    d_obj = datetime.strptime(p["current_date"], "%Y-%m-%d")
    is_match = d_obj.day % 6 == 0
    calendar_days = build_calendar_days(p["current_date"])
    return render_template("index.html", p=p, is_match=is_match, calendar_days=calendar_days, datetime=datetime)


@app.route("/play_match")
def play_match():
    p = load_data()
    if not p:
        return redirect(url_for("landing"))
    if p["age"] >= 39:
        return "Your career has ended. Time to retire, Legend."
    if p.get("injury", {}).get("days", 0) > 0 and p.get("fitness", 100) < 35:
        p["coach_note"] = "You are not cleared to play today. Rest or visit physio."
        save_data(p)
        return redirect(url_for("game"))

    if "active_match" not in p:
        p["active_match"] = {
            "pitch": random.choice(["Dusty & Cracked", "Hard & Bouncy", "Green Top", "Flat Road"]),
            "opponent": random.choice(["Titans", "Strikers", "Warriors"]),
            "step": 0,
            "questions": select_match_scenarios(p["role"]),
            "results": [],
            "runs": 0,
            "wickets": 0,
        }
        save_data(p)

    match = p["active_match"]
    if match["step"] >= len(match["questions"]):
        return redirect(url_for("match_summary"))

    scenario = match["questions"][match["step"]]
    return render_template(
        "pre_match.html",
        p=p,
        match=match,
        scenario=scenario,
        scene_label=SCENE_LABELS.get(scenario["scene"], "Match Moment"),
    )


@app.route("/process_match", methods=["POST"])
def process_match():
    return redirect(url_for("play_match"))


@app.route("/match_choice", methods=["POST"])
def match_choice():
    p = load_data()
    if not p:
        return redirect(url_for("landing"))

    match = p.get("active_match")
    if not match:
        return redirect(url_for("play_match"))

    step = match["step"]
    if step >= len(match["questions"]):
        return redirect(url_for("match_summary"))

    scenario = match["questions"][step]
    choice_index = int(request.form.get("choice_index", 0))
    selected = scenario["choices"][max(0, min(choice_index, len(scenario["choices"]) - 1))]
    effects = selected["effects"]

    apply_choice_effects(p, effects)
    match["runs"] += effects.get("runs", 0)
    match["wickets"] += effects.get("wickets", 0)
    match["results"].append({
        "scene": scenario["scene"],
        "title": scenario["title"],
        "decision": selected["label"],
        "outcome": selected["outcome"],
        "quality": selected["quality"],
        "effects": effects,
    })
    match["step"] += 1

    if match["step"] >= len(match["questions"]):
        p["stats"]["matches"] += 1
        advance_player_day(p)
        save_data(p)
        return redirect(url_for("match_summary"))

    save_data(p)
    return redirect(url_for("play_match"))


@app.route("/match_summary")
def match_summary():
    p = load_data()
    if not p:
        return redirect(url_for("landing"))

    match = p.get("active_match")
    if not match:
        return redirect(url_for("game"))

    results = match.get("results", [])
    impact_score = sum(2 if r["quality"] == "good" else -1 if r["quality"] == "bad" else 1 for r in results)
    verdict = "Excellent decisions" if impact_score >= 4 else "Solid match" if impact_score >= 1 else "Learning day"

    p["last_match"] = {
        "opponent": match["opponent"],
        "pitch": match["pitch"],
        "runs": match["runs"],
        "wickets": match["wickets"],
        "results": results,
        "verdict": verdict,
    }
    apply_post_match_story(p, p["last_match"], impact_score)
    del p["active_match"]
    save_data(p)
    return render_template("scorecard.html", p=p, match=p["last_match"])


@app.route("/advance_day")
def advance_day():
    p = load_data()
    if not p:
        return redirect(url_for("landing"))

    p["confidence"] = max(0, p["confidence"] - 2)
    update_injury(p)
    advance_player_day(p)
    save_data(p)
    return redirect(url_for("game"))


@app.route("/training/<type>")
def training(type):
    p = load_data()
    if not p:
        return redirect(url_for("landing"))
    options = TRAINING_OPTIONS.get(type)
    if not options:
        return redirect(url_for("game"))
    return render_template("training.html", p=p, training_type=type, options=options)


@app.route("/action/<type>/<focus>")
def focused_action(type, focus):
    p = load_data()
    if not p:
        return redirect(url_for("landing"))

    options = TRAINING_OPTIONS.get(type, [])
    selected = next((item for item in options if item["id"] == focus), None)
    if not selected:
        return redirect(url_for("game"))

    p["confidence"] = max(0, min(100, p["confidence"] + selected["confidence"]))
    p["stress"] = max(0, min(100, p["stress"] + selected["stress"]))
    p["fitness"] = max(0, min(100, p["fitness"] + selected["fitness"]))
    p.setdefault("training_log", []).insert(0, f"{selected['label']}: {selected['note']}")
    p["training_log"] = p["training_log"][:5]
    p["coach_note"] = f"Training focus completed: {selected['label']}."
    if type == "rest":
        update_injury(p)
    advance_player_day(p)
    save_data(p)
    return redirect(url_for("game"))


@app.route("/action/<type>")
def action(type):
    p = load_data()
    if not p:
        return redirect(url_for("landing"))

    if type == "nets":
        p["stress"] = min(100, p["stress"] + 25)
        p["confidence"] = min(100, p["confidence"] + 20)
    elif type == "gym":
        p["fitness"] = min(100, p["fitness"] + 10)
        p["stress"] = min(100, p["stress"] + 5)
    elif type == "rest":
        p["stress"] = max(0, p["stress"] - 20)
        p["fitness"] = min(100, p["fitness"] + 5)

    p["confidence"] = max(0, p["confidence"] - 2)

    advance_player_day(p)
    save_data(p)
    return redirect(url_for("game"))


@app.route("/api/play-delivery", methods=["POST"])
def play_delivery():
    data = request.get_json()
    player_intent = data.get("player_intent")
    batting_action = data.get("batting_action")

    if not player_intent or not batting_action:
        return jsonify({"error": "Missing player_intent or batting_action"}), 400

    pitch_modifiers = {
        "Green Top": {"risk_mult": 1.25, "run_mult": 0.95},
        "Dust Bowl": {"risk_mult": 1.30, "run_mult": 0.90},
        "Flat Track": {"risk_mult": 0.85, "run_mult": 1.15},
    }
    p_mod = pitch_modifiers.get(CURRENT_MATCH_PITCH, {"risk_mult": 1.0, "run_mult": 1.0})
    base_probability = [35, 30, 15, 12, 5, 3]

    if player_intent == "Defensive":
        base_probability = [85, 12, 2, 0, 0, 1] if batting_action == "Defend" else [65, 25, 5, 3, 0, 2]
    elif player_intent == "Steady":
        if batting_action in ["Drive", "Pull"]:
            base_probability = [30, 40, 18, 10, 0, 2]
        elif batting_action == "Defend":
            base_probability = [70, 25, 3, 0, 0, 2]
        elif batting_action == "Lofted":
            base_probability = [25, 20, 15, 25, 10, 5]
    elif player_intent == "Attacking":
        if batting_action == "Lofted":
            base_probability = [15, 10, 10, 30, 25, 10]
        elif batting_action in ["Drive", "Pull"]:
            base_probability = [20, 25, 15, 28, 5, 7]
        elif batting_action == "Defend":
            base_probability = [50, 40, 5, 2, 0, 3]

    modified_prob = list(base_probability)
    modified_prob[5] = max(1, round(modified_prob[5] * p_mod["risk_mult"]))
    modified_prob[3] = round(modified_prob[3] * p_mod["run_mult"])
    modified_prob[4] = round(modified_prob[4] * p_mod["run_mult"])
    modified_prob[0] = max(0, 100 - sum(modified_prob[1:]))

    outcomes = ["0", "1", "2", "4", "6", "Wicket"]
    selected_outcome = random.choices(outcomes, weights=modified_prob, k=1)[0]
    commentary = generate_commentary(selected_outcome, batting_action, CURRENT_MATCH_PITCH)

    return jsonify({
        "outcome": selected_outcome,
        "commentary": commentary,
        "pitch_played_on": CURRENT_MATCH_PITCH,
        "probabilities_used": {
            "dot": modified_prob[0],
            "singles_doubles": modified_prob[1] + modified_prob[2],
            "boundaries": modified_prob[3] + modified_prob[4],
            "wicket": modified_prob[5],
        },
    })


def generate_commentary(outcome, action, pitch):
    if outcome == "Wicket":
        if pitch == "Dust Bowl":
            return f"OUT! The ball gripped on this {pitch} track. The batter attempted a {action} but misread the turn."
        return f"OUT! Caught behind. An aggressive {action} flashes outside off stump and takes an edge."
    if outcome == "4":
        return f"FOUR runs! Superb execution from a clean {action}."
    if outcome == "6":
        return f"SIX RUNS! Clears the rope with a towering {action}."
    if outcome in ["1", "2"]:
        return f"Safely pushed away with a steady {action}."
    return "Defended confidently. No run taken."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
