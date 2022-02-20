import streamlit as st
import json
import datetime as dt

def save():
    json.dump(points,open("points.json","w"))
    json.dump(habits,open("habits.json","w"))
    json.dump(rewards,open("rewards.json","w"))
    st.experimental_rerun()
    

weekly_points = 70
    
points = json.load(open("points.json"))

habits = json.load(open("habits.json"))

rewards = json.load(open("rewards.json"))

def trash():
    if st.button('Reset'):
        # print is visible in the server output, not in the page
        json.dump({"total":0},open("points.json","w"))
        json.dump({},open("habits.json","w"))
        json.dump({},open("rewards.json","w"))
        st.experimental_rerun()

st.write("## Points:")

st.write(f'### {points["total"]}')

if habits:
    st.write("## Habits:")
habits_st = {key:{} for key in habits.keys()}
for key,habit in habits_st.items():
    habit["expander"] = st.expander(habits[key]["name"])

    start = dt.date.today() - dt.timedelta(days=dt.date.today().weekday())
    for day in range(7):
        habits[key]["counts"][str(start + dt.timedelta(day))] = habits[key]["counts"].get(str(start + dt.timedelta(day)),0)

    if habits[key]["type"] == "Time Based":
        count_type = "hours "

        habit["main"] = habit["expander"].columns([2,2,1])

        hours = habit["main"][0].number_input('Hours', 0,key=f'{habits[key]["name"]} hours')

        mins = habit["main"][1].number_input('Minutes', 0,key=f'{habits[key]["name"]} mins', step=5)

        habit["main"][2].write("# ")
        if habit["main"][2].button('Add Time',key=f'{habits[key]["name"]} add'):
            # print is visible in the server output, not in the page
            habits[key]["counts"][str(dt.date.today())] += int(mins) + 60*int(hours)
            points["total"] += weekly_points*(int(mins) + 60*int(hours))/(len(habits)*60*float(habits[key]["goal"]))
            save()

        count = sum(habits[key]["counts"].values())/60

    else:
        count_type = ""

        if habit["expander"].button('+',key=f'{habits[key]["name"]} add'):
            habits[key]["counts"][str(dt.date.today())] += 1
            points["total"] += weekly_points/(len(habits)*float(habits[key]["goal"]))
            save()
        count = sum(habits[key]["counts"].values())

    habit["expander"].bar_chart(pd.DataFrame(habits[key]["counts"].values(),index=habits[key]["counts"].keys()))

    habit["expander"].write(f'### {count} out of {habits[key]["goal"]} {count_type}complete this week')

    habit["expander"].write("# ")
    habit["end_columns"] = habit["expander"].columns([4,1])

    if habit["end_columns"][1].button('Delete Habit',f'{habits[key]["name"]} delete'):
        del habits[key]
        save()

if rewards:
    st.write("## Rewards:")

reward_sts = {key:{} for key in rewards.keys()}
for key,reward in rewards.items():
    reward_st = reward_sts[key]
    
    if reward["type"] == "Count Based":
        reward_st["columns"] = st.columns([3.5,0.5,1])
        reward_st["columns"][0].write(f"##### ")
        reward_st["columns"][0].write(f"##### ")
        reward_st["columns"][0].write(f"##### {key}")
        reward_st["columns"][0].write(f"##### ")
        reward_st["columns"][0].write(f"##### ")
        reward_st["columns"][1].write(f"##### ")
        reward_st["columns"][1].write(f"##### ")
        reward_st["columns"][1].write(f'##### {reward["points"]}')
        reward_st["columns"][1].write(f"##### ")
        reward_st["columns"][1].write(f"##### ")
        reward_st["columns"][2].write(f"##### ")
        reward_st["columns"][2].write(f"##### ")
        if reward["points"] <= points["total"]:
            if reward_st["columns"][2].button("Use", key=f'{key} use'):
                points["total"] += -reward["points"]
                save()
        else:
            reward_st["columns"][2].write('Not enough')
        reward_st["columns"][2].write(f"##### ")
        reward_st["columns"][2].write(f"##### ")
    else:
        reward_st["columns"] = st.columns([1.2,1.1,1.1,0.5,1])
        reward_st["columns"][0].write(f"##### ")
        reward_st["columns"][0].write(f"##### ")
        reward_st["columns"][0].write(f"##### {key}")
        reward_st["columns"][0].write(f"##### ")
        reward_st["columns"][0].write(f"##### ")
        reward_st["hours"] = reward_st["columns"][1].number_input('Hours', 0,key=f'{key} reward hours')
        reward_st["minutes"] = reward_st["columns"][2].number_input('Minutes', 0, step=5,key=f'{key} reward minutes')
        cost = round(reward["points"] * (reward_st["hours"]+reward_st["minutes"]/60),2)
        reward_st["columns"][3].write(f"##### ")
        reward_st["columns"][3].write(f"##### ")
        reward_st["columns"][3].write(f'##### {cost}')
        reward_st["columns"][3].write(f"##### ")
        reward_st["columns"][3].write(f"##### ")
        reward_st["columns"][4].write(f"##### ")
        reward_st["columns"][4].write(f"##### ")
        if cost <= points["total"]:
            if reward_st["columns"][4].button("Use", key=f'{key} use'):
                points["total"] += -cost
                save()
        else:
            reward_st["columns"][4].write('Not enough')
        reward_st["columns"][4].write(f"##### ")
        reward_st["columns"][4].write(f"##### ")

st.write("## Add Habit:")

new_habit = st.columns([1.8,1.1,1.1,1])

name = new_habit[0].text_input('Name', '')

goal = new_habit[1].number_input('Weekly Goal', 0)

option = new_habit[2].selectbox('Type',["Time Based","Count Based"])

new_habit[3].write("# ")
if new_habit[3].button('Add Habbit'):
    # print is visible in the server output, not in the page
    if name and goal:
        habits[name] = {"name":name, "goal":goal, "type":option, "counts":{}}
        save()
    else:
        pass


st.write("## Add Reward:")

new_reward = st.columns([1.9,1.1,1.1,1])

reward_name = new_reward[0].text_input('Name', '', key="reward name")

reward_points = new_reward[1].number_input('Points', 0)

reward_option = new_reward[2].selectbox('Type',["Time Based","Count Based"], key="reward type")

new_reward[3].write("# ")
if new_reward[3].button('Add Reward'):
    # print is visible in the server output, not in the page
    if reward_name and reward_points:
        rewards[reward_name] = {"points":reward_points, "type":reward_option}
        save()
    else:
        pass