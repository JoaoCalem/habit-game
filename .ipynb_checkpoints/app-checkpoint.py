import streamlit as st
import json
import datetime as dt
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib

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

def update_points(points):
    cur.execute(f"SELECT total FROM points")
    cur.execute(f"UPDATE points SET total={float(cur.fetchone()[0]) + points}")
    for reward in rewards.keys():
        cur.execute(f"SELECT count FROM rewards WHERE id={reward}")
        cur.execute(f"UPDATE rewards SET count={float(cur.fetchone()[0]) + points} WHERE id={reward}")
    save()
    
    
conn = sql_connection()

cur = conn.cursor()
    
weekly_points = 100
    
cur.execute("SELECT * FROM points")

start = dt.date.today() - dt.timedelta(days=dt.date.today().weekday())
points_query = cur.fetchone()
if str(start) != str(points_query[2]):
    cur.execute(f"UPDATE points SET date='{start}'")
    cur.execute(f"UPDATE points SET total=0")
    cur.execute(f"DELETE FROM counts")
    save()
    
points = points_query[1]

cur.execute("SELECT * FROM habits")
habits = {r[0]: {"name": r[1], "goal":r[2], "daily_goal":r[4], "type":r[3]} for r in cur.fetchall()}

cur.execute("SELECT * FROM rewards")
rewards = {r[0]: {"name": r[1],"points":r[2], "type":r[3], "accum":r[4],"count":r[5]} for r in cur.fetchall()}

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

st.write(f'### {points//1}')

if habits:
    st.write("## Habits:")
habits_st = {key:{} for key in habits.keys()}
for key,habit in habits_st.items():
    habit["expander"] = st.expander(habits[key]["name"])
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
            if daily_goal:
                if daily_goal > count_today and daily_goal <= temp/60:
                    daily_goal_points = weekly_points/(len(habits)*28)
                    
                normal_modifier = 2
            else:
                normal_modifier = 4/3
           
            weekly_goal = float(habits[key]["goal"])
            if weekly_goal > count and weekly_goal <= count + int(mins)/60 + int(hours):
                weekly_goal_points = weekly_points/(len(habits)*4)
            
            update_points(weekly_points*(int(mins)/60 + int(hours))\
                /(len(habits)*weekly_goal*normal_modifier) + daily_goal_points + weekly_goal_points)
            

    else:
        count_type = ""
        
        cur.execute(f"SELECT c.date, c.count FROM counts c WHERE date >= '{start}' AND habit_id={key}")
        temp_counts = {str(i[0]):float(i[1]) for i in cur.fetchall()}
        count = sum(temp_counts.values())

        if habit["expander"].button('+',key=f'{habits[key]["name"]} add'):
            
            count_today = temp_counts[str(dt.date.today())]
            cur.execute(f"""UPDATE counts SET count={count_today+1}
                WHERE habit_id = {key} AND date = '{dt.date.today()}'""")
            
            daily_goal = float(habits[key]["daily_goal"])
            if daily_goal:
                if daily_goal > count_today and daily_goal <= count_today + 1:
                    daily_goal_points = weekly_points/(len(habits)*28)

                normal_modifier = 2
            else:
                normal_modifier = 4/3
           
            weekly_goal = float(habits[key]["goal"])
            if weekly_goal > count and weekly_goal <= count + 1:
                weekly_goal_points = weekly_points/(len(habits)*4)
            
            update_points(weekly_points/(len(habits)*weekly_goal*normal_modifier)\
                + daily_goal_points + weekly_goal_points)
    
    @st.cache(hash_funcs={matplotlib.figure.Figure: hash})
    def plot(temp_counts,habits):
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
        return fig
        
    fig = plot(temp_counts,habits)
    
    habit["expander"].write(fig)

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
    reward_st["expander"] = st.expander(reward['name'])
    
    if reward["type"] == "Count Based":
        reward_st["expander"].write(f'##### Available: {round(reward["count"],2)}')
        if reward["points"] <= reward["count"]:
            if reward_st["expander"].button(f"Use {reward['points']}", key=f'{key} use'):
                cur.execute(f"SELECT count FROM rewards WHERE id={key}")
                cur.execute(f"UPDATE rewards SET count={float(cur.fetchone()[0]) - reward['points']} WHERE id={key}")
                
                save()
        else:
            reward_st["expander"].write('Not enough')
    else:
        reward_st["hours"] = reward_st["expander"].number_input('Hours', 0,key=f'{key} reward hours')
        reward_st["minutes"] = reward_st["expander"].number_input('Minutes', 0, step=5,key=f'{key} reward minutes')
        cost = round(reward["points"] * (reward_st["hours"]+reward_st["minutes"]/60),2)
        reward_st["expander"].write(f'##### Available: {round(reward["count"],2)}')
        if cost <= reward["count"]:
            if reward_st["expander"].button(f"Use {cost}", key=f'{key} use'):
                cur.execute(f"SELECT count FROM rewards WHERE id={key}")
                cur.execute(f"UPDATE rewards SET count={float(cur.fetchone()[0]) - cost} WHERE id={key}")
                
                save()
        else:
            reward_st["expander"].write('Not enough')

st.write("## Add Habit:")

name = st.text_input('Name', '')

new_habit = st.columns([1.1,1.1,1.1,1])

goal = new_habit[0].number_input('Weekly Goal', 0)

daily_goal = new_habit[1].number_input('Daily Goal', 0)

option = new_habit[2].selectbox('Type',["Time Based","Count Based"])

new_habit[3].write("# ")
if new_habit[3].button('Add Habbit'):
    # print is visible in the server output, not in the page
    if name and goal:
        cur.execute(f"INSERT INTO habits (name,daily_goal,goal,type) VALUES ('{name}', '{daily_goal}','{goal}','{option}')")
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