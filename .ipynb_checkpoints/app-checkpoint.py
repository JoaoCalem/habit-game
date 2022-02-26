import streamlit as st
import json
import datetime as dt
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns

@st.cache(allow_output_mutation=True, hash_funcs={"_thread.RLock": lambda _: None})
def sql_connection():
    conn = psycopg2.connect(
    host="ec2-54-83-21-198.compute-1.amazonaws.com",
    database="d5nu5a60baen6j",
    user="yucdrxbhlqsiku",
    password="2d63af339af82fc84dfa28985910c1fd2b423d7dd3618a6cc24926928d9e6571")

    return conn

def save():
    #json.dump(points,open("points.json","w"))
    #json.dump(habits,open("habits.json","w"))
    #json.dump(rewards,open("rewards.json","w"))
    conn.commit()
    st.experimental_rerun()
    
conn = sql_connection()

cur = conn.cursor()
    
weekly_points = 100
    
cur.execute("SELECT * FROM points")
points = cur.fetchone()[1]

cur.execute("SELECT * FROM habits")
habits = {r[0]: {"name": r[1], "goal":r[2], "daily_goal":r[4], "type":r[3]} for r in cur.fetchall()}

cur.execute("SELECT * FROM rewards")
rewards = {r[0]: {"name": r[1],"points":r[2], "type":r[3]} for r in cur.fetchall()}

cur.execute("SELECT * FROM counts")
counts = cur.fetchall()

def trash():
    if st.button('Reset'):
        # print is visible in the server output, not in the page
        #json.dump({"total":0},open("points.json","w"))
        #json.dump({},open("habits.json","w"))
        #json.dump({},open("rewards.json","w"))

        conn.rollback()
        conn.close()
        st.experimental_rerun()

st.write("## Points:")

st.write(f'### {round(points,2)}')

if habits:
    st.write("## Habits:")
habits_st = {key:{} for key in habits.keys()}
for key,habit in habits_st.items():
    habit["expander"] = st.expander(habits[key]["name"])

    start = dt.date.today() - dt.timedelta(days=dt.date.today().weekday())
    for day in range(7):
        day_datetime = start + dt.timedelta(day)
        cur.execute(f"SELECT * FROM counts WHERE habit_id = {key} AND date = '{day_datetime}'")
        if not cur.fetchone():
            cur.execute(f"INSERT INTO counts (habit_id, date, count) VALUES ({key}, '{day_datetime}', 0)")
    
    daily_goal_points = 0
    weekly_goal_points = 0
    
    if habits[key]["type"] == "Time Based":
        count_type = "hours "

        habit["main"] = habit["expander"].columns([2,2,1])

        hours = habit["main"][0].number_input('Hours', 0,key=f'{habits[key]["name"]} hours')

        mins = habit["main"][1].number_input('Minutes', 0,key=f'{habits[key]["name"]} mins', step=5)
        
        cur.execute(f"SELECT c.date, c.count/60 FROM counts c WHERE date >= '{start}' AND habit_id={key}")
        temp_counts = {str(i[0]):float(i[1]) for i in cur.fetchall()}
        count = sum(temp_counts.values())
        
        habit["main"][2].write("# ")
        if habit["main"][2].button('Add Time',key=f'{habits[key]["name"]} add'):
            
            count_today = temp_counts[str(dt.date.today())]
            temp = count_today*60 + int(mins) + 60*int(hours)
            
            cur.execute(f"""UPDATE counts SET count={temp}
                WHERE habit_id = {key} AND date = '{dt.date.today()}'""")
            
            daily_goal = float(habits[key]["daily_goal"])
            passed_daily = all([
                daily_goal,
                daily_goal > count_today,
                daily_goal <= temp/60
            ])
            
            if passed_daily:
                daily_goal_points = weekly_points/(len(habits)*28)
                print(daily_goal_points)
            
            if daily_goal:
                normal_modifier = 2
            else:
                normal_modifier = 4/3
           
            weekly_goal = float(habits[key]["goal"])
            passed_weekly = all([
                weekly_goal > count,
                weekly_goal <= count + int(mins)/60 + int(hours)
            ])
            
            if passed_weekly:
                weekly_goal_points = weekly_points/(len(habits)*4)
            
            cur.execute(f"SELECT total FROM points")
            temp = float(cur.fetchone()[0]) + weekly_points*(int(mins) + 60*int(hours))\
                /(len(habits)*60*float(habits[key]["goal"])*normal_modifier)\
                + daily_goal_points + weekly_goal_points
                
            cur.execute(f"UPDATE points SET total={temp}")
            
            save()

    else:
        count_type = ""
        
        cur.execute(f"SELECT c.date, c.count FROM counts c WHERE date >= '{start}' AND habit_id={key}")
        temp_counts = {str(i[0]):float(i[1]) for i in cur.fetchall()}
        count = sum(temp_counts.values())

        if habit["expander"].button('+',key=f'{habits[key]["name"]} add'):
            cur.execute(f"SELECT count FROM counts WHERE habit_id = {key} AND date = '{dt.date.today()}'")
            temp = float(cur.fetchone()[0]) + 1
            cur.execute(f"""UPDATE counts SET count={temp}
                WHERE habit_id = {key} AND date = '{dt.date.today()}'""")
            
            cur.execute(f"SELECT total FROM points")
            temp = float(cur.fetchone()[0]) + weekly_points/(len(habits)*float(habits[key]["goal"]))
            cur.execute(f"UPDATE points SET total={temp}")
            
            save()
    
    fig, ax = plt.subplots()
    fig.set_figheight(2)
    df = pd.DataFrame(temp_counts.values(),index=temp_counts.keys(), columns=["Count"]).sort_index()
    sns.barplot(data=df,x=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],y="Count",ax=ax, color="black")
    ylim_min = float(habits[key]["daily_goal"])*1.3
    if ax.get_ylim()[1] < ylim_min:
        ax.set_ylim([0,ylim_min])
    
    ax2 = plt.twinx()
    ax2.plot(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],[habits[key]["daily_goal"]]*7)
    ax2.set_ylim(ax.get_ylim())

    habit["expander"].pyplot(fig)

    habit["expander"].write(f'### {round(count,2)} out of {habits[key]["goal"]} {count_type}complete this week')

    habit["expander"].write("# ")
    habit["end_columns"] = habit["expander"].columns([4,1])

    if habit["end_columns"][1].button('Delete Habit',f'{habits[key]["name"]} delete'):
        cur.execute(f"DELETE FROM counts WHERE habit_id={key}")
        cur.execute(f"DELETE FROM habits WHERE id={key}")
        save()
    conn.commit()

if rewards:
    st.write("## Rewards:")

reward_sts = {key:{} for key in rewards.keys()}
for key,reward in rewards.items():
    reward_st = reward_sts[key]
    reward["points"] = float(reward["points"])
    
    if reward["type"] == "Count Based":
        reward_st["columns"] = st.columns([3.5,0.5,1])
        reward_st["columns"][0].write(f"##### ")
        reward_st["columns"][0].write(f"##### ")
        reward_st["columns"][0].write(f"##### {reward['name']}")
        reward_st["columns"][0].write(f"##### ")
        reward_st["columns"][0].write(f"##### ")
        reward_st["columns"][1].write(f"##### ")
        reward_st["columns"][1].write(f"##### ")
        reward_st["columns"][1].write(f'##### {reward["points"]}')
        reward_st["columns"][1].write(f"##### ")
        reward_st["columns"][1].write(f"##### ")
        reward_st["columns"][2].write(f"##### ")
        reward_st["columns"][2].write(f"##### ")
        if reward["points"] <= points:
            if reward_st["columns"][2].button("Use", key=f'{key} use'):
                cur.execute(f"SELECT total FROM points")
                temp = float(cur.fetchone()[0]) - reward["points"]
                cur.execute(f"UPDATE points SET total={temp}")
                
                save()
        else:
            reward_st["columns"][2].write('Not enough')
        reward_st["columns"][2].write(f"##### ")
        reward_st["columns"][2].write(f"##### ")
    else:
        reward_st["columns"] = st.columns([1.2,1.1,1.1,0.5,1])
        reward_st["columns"][0].write(f"##### ")
        reward_st["columns"][0].write(f"##### ")
        reward_st["columns"][0].write(f"##### {reward['name']}")
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
        if cost <= points:
            if reward_st["columns"][4].button("Use", key=f'{key} use'):
                cur.execute(f"SELECT total FROM points")
                temp = float(cur.fetchone()[0]) - cost
                cur.execute(f"UPDATE points SET total={temp}")
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
        cur.execute(f"INSERT INTO habits (name,goal,type) VALUES ('{name}','{goal}','{option}')")
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
        cur.execute(f"""INSERT INTO rewards (name,points,type)
            VALUES ('{reward_name}','{reward_points}','{reward_option}')""")
        save()
    else:
        pass