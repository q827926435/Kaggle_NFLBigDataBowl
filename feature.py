import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
import datetime
# from kaggle.competitions import nflrush
import tqdm
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, KFold
import keras

from tqdm import tqdm_notebook
import warnings
import os

from NFLBigDataBowl import model_NN
from sklearn.model_selection import train_test_split, KFold


def init_setting():
    warnings.filterwarnings('ignore')
    pd.set_option('expand_frame_repr', False)
    pd.set_option('display.max_rows', 200)
    pd.set_option('display.max_columns', 200)
    sns.set_style('darkgrid')
    mpl.rcParams['figure.figsize'] = [15, 10]


# 提交的作品将根据连续排列的概率分数(CRPS)进行评估。
# 对于每个PlayId，您必须预测获得或丢失码数的累积概率分布。换句话说，您预测的每一列表示该队在比赛中获得<=那么多码的概率。
def return_step(x):
    temp = np.zeros(199)
    temp[x + 99:] = 1
    return temp


def strtoseconds(txt):
    txt = txt.split(':')
    ans = int(txt[0]) * 60 + int(txt[1]) + int(txt[2]) / 60
    return ans


def strtofloat(x):
    try:
        return float(x)
    except:
        return -1


def map_weather(txt):
    ans = 1
    if pd.isna(txt):
        return 0
    if 'partly' in txt:
        ans *= 0.5
    if 'climate controlled' in txt or 'indoor' in txt:
        return ans * 3
    if 'sunny' in txt or 'sun' in txt:
        return ans * 2
    if 'clear' in txt:
        return ans
    if 'cloudy' in txt:
        return -ans
    if 'rain' in txt or 'rainy' in txt:
        return -2 * ans
    if 'snow' in txt:
        return -3 * ans
    return 0


def OffensePersonnelSplit(x):
    dic = {'DB': 0, 'DL': 0, 'LB': 0, 'OL': 0, 'QB': 0, 'RB': 0, 'TE': 0, 'WR': 0}
    for xx in x.split(","):
        xxs = xx.split(" ")
        dic[xxs[-1]] = int(xxs[-2])
    return dic


def DefensePersonnelSplit(x):
    dic = {'DB': 0, 'DL': 0, 'LB': 0, 'OL': 0}
    for xx in x.split(","):
        xxs = xx.split(" ")
        dic[xxs[-1]] = int(xxs[-2])
    return dic


def orientation_to_cat(x):
    x = np.clip(x, 0, 360 - 1)
    try:
        return str(int(x / 15))
    except:
        return "nan"


def preprocess(train):
    ## GameClock
    train['GameClock_sec'] = train['GameClock'].apply(strtoseconds)
    train["GameClock_minute"] = train["GameClock"].apply(lambda x: x.split(":")[0]).astype("object")  # hour

    ## Height
    train['PlayerHeight_dense'] = train['PlayerHeight'].apply(
        lambda x: 12 * int(x.split('-')[0]) + int(x.split('-')[1]))

    ## Time
    train['TimeHandoff'] = train['TimeHandoff'].apply(lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%fZ"))
    train['TimeSnap'] = train['TimeSnap'].apply(lambda x: datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S.%fZ"))

    train['TimeDelta'] = train.apply(lambda row: (row['TimeHandoff'] - row['TimeSnap']).total_seconds(), axis=1)
    train['PlayerBirthDate'] = train['PlayerBirthDate'].apply(lambda x: datetime.datetime.strptime(x, "%m/%d/%Y"))

    ## Age
    seconds_in_year = 60 * 60 * 24 * 365.25
    train['PlayerAge'] = train.apply(
        lambda row: (row['TimeHandoff'] - row['PlayerBirthDate']).total_seconds() / seconds_in_year, axis=1)
    train["PlayerAge_ob"] = train['PlayerAge'].astype(np.int).astype("object")

    ## WindSpeed
    # print(train['WindSpeed'].value_counts())
    train['WindSpeed_ob'] = train['WindSpeed'].apply(
        lambda x: x.lower().replace('mph', '').strip() if not pd.isna(x) else x)
    train['WindSpeed_ob'] = train['WindSpeed_ob'].apply(
        lambda x: (int(x.split('-')[0]) + int(x.split('-')[1])) / 2 if not pd.isna(x) and '-' in x else x)
    train['WindSpeed_ob'] = train['WindSpeed_ob'].apply(
        lambda x: (int(x.split()[0]) + int(x.split()[-1])) / 2 if not pd.isna(x) and type(
            x) != float and 'gusts up to' in x else x)
    train['WindSpeed_dense'] = train['WindSpeed_ob'].apply(strtofloat)

    ## Weather
    train['GameWeather_process'] = train['GameWeather'].str.lower()
    train['GameWeather_process'] = train['GameWeather_process'].apply(
        lambda x: "indoor" if not pd.isna(x) and "indoor" in x else x)
    train['GameWeather_process'] = train['GameWeather_process'].apply(
        lambda x: x.replace('coudy', 'cloudy').replace('clouidy', 'cloudy').replace('party', 'partly') if not pd.isna(
            x) else x)
    train['GameWeather_process'] = train['GameWeather_process'].apply(
        lambda x: x.replace('clear and sunny', 'sunny and clear') if not pd.isna(x) else x)
    train['GameWeather_process'] = train['GameWeather_process'].apply(
        lambda x: x.replace('skies', '').replace("mostly", "").strip() if not pd.isna(x) else x)
    train['GameWeather_dense'] = train['GameWeather_process'].apply(map_weather)

    ## Rusher
    train['IsRusher'] = (train['NflId'] == train['NflIdRusher'])
    train['IsRusher_ob'] = (train['NflId'] == train['NflIdRusher']).astype("object")
    temp = train[train["IsRusher"]][["Team", "PlayId"]].rename(columns={"Team": "RusherTeam"})
    train = train.merge(temp, on="PlayId")
    train["IsRusherTeam"] = train["Team"] == train["RusherTeam"]

    ## dense -> categorical
    train["Quarter_ob"] = train["Quarter"].astype("object")
    train["Down_ob"] = train["Down"].astype("object")
    train["JerseyNumber_ob"] = train["JerseyNumber"].astype("object")
    train["YardLine_ob"] = train["YardLine"].astype("object")
    # train["DefendersInTheBox_ob"] = train["DefendersInTheBox"].astype("object")
    # train["Week_ob"] = train["Week"].astype("object")
    # train["TimeDelta_ob"] = train["TimeDelta"].astype("object")

    ## Orientation and Dir
    train["Orientation_ob"] = train["Orientation"].apply(lambda x: orientation_to_cat(x)).astype("object")
    train["Dir_ob"] = train["Dir"].apply(lambda x: orientation_to_cat(x)).astype("object")

    train["Orientation_sin"] = train["Orientation"].apply(lambda x: np.sin(x / 360 * 2 * np.pi))
    train["Orientation_cos"] = train["Orientation"].apply(lambda x: np.cos(x / 360 * 2 * np.pi))
    train["Dir_sin"] = train["Dir"].apply(lambda x: np.sin(x / 360 * 2 * np.pi))
    train["Dir_cos"] = train["Dir"].apply(lambda x: np.cos(x / 360 * 2 * np.pi))

    ## diff Score
    train["diffScoreBeforePlay"] = train["HomeScoreBeforePlay"] - train["VisitorScoreBeforePlay"]
    train["diffScoreBeforePlay_binary_ob"] = (train["HomeScoreBeforePlay"] > train["VisitorScoreBeforePlay"]).astype(
        "object")

    ## Turf
    Turf = {'Field Turf': 'Artificial', 'A-Turf Titan': 'Artificial', 'Grass': 'Natural',
            'UBU Sports Speed S5-M': 'Artificial', 'Artificial': 'Artificial', 'DD GrassMaster': 'Artificial',
            'Natural Grass': 'Natural', 'UBU Speed Series-S5-M': 'Artificial', 'FieldTurf': 'Artificial',
            'FieldTurf 360': 'Artificial', 'Natural grass': 'Natural', 'grass': 'Natural', 'Natural': 'Natural',
            'Artifical': 'Artificial', 'FieldTurf360': 'Artificial', 'Naturall Grass': 'Natural',
            'Field turf': 'Artificial', 'SISGrass': 'Artificial', 'Twenty-Four/Seven Turf': 'Artificial',
            'natural grass': 'Natural'}
    train['Turf'] = train['Turf'].map(Turf)

    ## OffensePersonnel
    temp = train["OffensePersonnel"].iloc[np.arange(0, len(train), 22)].apply(
        lambda x: pd.Series(OffensePersonnelSplit(x)))
    temp.columns = ["Offense" + c for c in temp.columns]
    temp["PlayId"] = train["PlayId"].iloc[np.arange(0, len(train), 22)]
    train = train.merge(temp, on="PlayId")

    ## DefensePersonnel
    temp = train["DefensePersonnel"].iloc[np.arange(0, len(train), 22)].apply(
        lambda x: pd.Series(DefensePersonnelSplit(x)))
    temp.columns = ["Defense" + c for c in temp.columns]
    temp["PlayId"] = train["PlayId"].iloc[np.arange(0, len(train), 22)]
    train = train.merge(temp, on="PlayId")

    ## DisplayName remove Outlier
    v = train["DisplayName"].value_counts()
    missing_values = list(v[v < 5].index)
    train["DisplayName"] = train["DisplayName"].where(~train["DisplayName"].isin(missing_values),
                                                      "nan")  # 如果 cond 为真，保持原来的值，否则替换为other

    ## PlayerCollegeName remove Outlier
    v = train["PlayerCollegeName"].value_counts()
    missing_values = list(v[v < 10].index)
    train["PlayerCollegeName"] = train["PlayerCollegeName"].where(~train["PlayerCollegeName"].isin(missing_values),
                                                                  "nan")

    ## sort
    #     train = train.sort_values(by = ['X']).sort_values(by = ['Dis']).sort_values(by=['PlayId', 'Team', 'IsRusher']).reset_index(drop = True)
    train = train.sort_values(by=['X']).sort_values(by=['Dis']).sort_values(
        by=['PlayId', 'IsRusherTeam', 'IsRusher']).reset_index(drop=True)
    # pd.to_pickle(train, "train.pkl")
    drop(train)
    return train


def split_dense_cat_feature(train):
    cat_features = []  # 标签型的
    dense_features = []  # 数值型的
    for col in train.columns:
        if train[col].dtype == 'object':
            cat_features.append(col)
            # print("*cat*", col, len(train[col].unique()))
        else:
            dense_features.append(col)
            # print("!dense!", col, len(train[col].unique()))
    dense_features.remove("PlayId")
    dense_features.remove("Yards")

    # categorical
    train_cat = train[cat_features]
    categories = []
    most_appear_each_categories = {}
    for col in tqdm_notebook(train_cat.columns):
        train_cat.loc[:, col] = train_cat[col].fillna("nan")
        train_cat.loc[:, col] = col + "__" + train_cat[col].astype(str)
        most_appear_each_categories[col] = list(train_cat[col].value_counts().index)[0]  # 取类别最多的
        categories.append(train_cat[col].unique())
    categories = np.hstack(categories)  # 所有不同种类的类别
    print(len(categories))

    le = LabelEncoder()
    le.fit(categories)
    # Label Encode,转化为数字标签
    for col in tqdm_notebook(train_cat.columns):
        train_cat.loc[:, col] = le.transform(train_cat[col])
    num_classes = len(le.classes_)
    print(num_classes)

    # Dense
    train_dense = train[dense_features]
    sss = {}
    medians = {}
    for col in tqdm_notebook(train_dense.columns):
        medians[col] = np.nanmedian(train_dense[col])  # 忽略Nan值后的中位数
        train_dense.loc[:, col] = train_dense[col].fillna(medians[col])
        ss = StandardScaler()
        train_dense.loc[:, col] = ss.fit_transform(train_dense[col].values[:, None])
        sss[col] = ss
    return train_dense, train_cat, num_classes


def drop(train):
    drop_cols = ["GameId", "GameWeather", "NflId", "Season", "NflIdRusher"]
    drop_cols += ['TimeHandoff', 'TimeSnap', 'PlayerBirthDate']
    drop_cols += ["Orientation", "Dir", 'WindSpeed', "GameClock"]
    drop_cols += ["DefensePersonnel", "OffensePersonnel"]
    train.drop(drop_cols, axis=1, inplace=True)
    return train


def get_NN_feature(train_dense, train_cat):
    # Divide features into groups
    ## dense features for play, 同一队伍里std为0即作为整个play的特征 (5,) ，如果是11则(11,)
    dense_game_features = train_dense.columns[train_dense[:22].std() == 0]
    ## dense features for each player (47,) 如果是11则(41,)
    dense_player_features = train_dense.columns[train_dense[:22].std() != 0]
    ## categorical features for play (14,) 如果是11则(15,)
    cat_game_features = train_cat.columns[train_cat[:22].std() == 0]
    ## categorical features for each player (5,) 如果是11则(4,)
    cat_player_features = train_cat.columns[train_cat[:22].std() != 0]

    # 23170*5 ,23170*22 = 总数据量，这里已经做了压缩
    train_dense_game = train_dense[dense_game_features].iloc[np.arange(0, len(train_dense), 22)].reset_index(drop=True)
    # train_dense_game = train_dense[dense_game_features].iloc[np.arange(0, len(train_dense), 22)].reset_index(drop=True).values
    ## with rusher player feature，22个人中只有一个是rusher，因此可以把rusher特征当成整个play的特征
    train_dense_game = pd.concat([train_dense_game, train_dense[dense_player_features][train_dense["IsRusher"] > 0].reset_index(drop=True)], axis=1)
    # train_dense_game = np.hstack([train_dense_game, train_dense[dense_player_features][train_dense["IsRusher"] > 0]])

    train_dense_players = [train_dense[dense_player_features].iloc[np.arange(k, len(train_dense), 22)].reset_index(drop=True)
                           for k in range(22)]
    train_dense_players = np.stack([t.values for t in train_dense_players]).transpose(1, 0, 2)  # 通过transpose()函数改变了x的索引值为（1，0，2），对应（y，x，z）

    train_cat_game = train_cat[cat_game_features].iloc[np.arange(0, len(train_dense), 22)].reset_index(drop=True)
    # train_cat_game = train_cat[cat_game_features].iloc[np.arange(0, len(train_dense), 22)].reset_index(drop=True).values
    train_cat_game = pd.concat(
        [train_cat_game, train_cat[cat_player_features][train_dense["IsRusher"] > 0].reset_index(drop=True)], axis=1)  ## with rusher player feature
        # [train_cat_game, train_cat[cat_player_features][train_dense["IsRusher"] > 0]])  ## with rusher player feature

    train_cat_players = [train_cat[cat_player_features].iloc[np.arange(k, len(train_dense), 22)].reset_index(drop=True) for k in range(22)]
    train_cat_players = np.stack([t.values for t in train_cat_players]).transpose(1, 0, 2)
    return train_dense_game, train_dense_players, train_cat_game, train_cat_players


def get_train_label(train):
    train_y = train["Yards"].iloc[np.arange(0, len(train), 22)].reset_index(drop=True)
    train_y_199 = np.vstack(train_y.apply(return_step).values)
    return train_y, train_y_199

def get_train_NN_data():
    path = 'cache_%s_train.csv' % os.path.basename(__file__)

    if os.path.exists(path):
        train = pd.read_csv(path)
        # print(len(data))
    else:
        train = pd.read_csv('data/train.csv', dtype={'WindSpeed': 'object'})
        train = preprocess(train)
        train.to_csv(path, index=False)

    train_dense, train_cat, num_classes_cat = split_dense_cat_feature(train)
    print(train_dense.shape, train_cat.shape, train.shape)  # (509762, 52) (509762, 19) (509762, 73)
    train_dense_game, train_dense_players, train_cat_game, train_cat_players = get_NN_feature(train_dense, train_cat)
    # print(train_dense_game.shape, train_dense_players.shape, train_cat_game.shape, train_cat_players.shape) # (23171, 52) (23171, 22, 47) (23171, 19) (23171, 22, 5)

    train_y, train_y_199 = get_train_label(train)
    # print(train_y_raw.shape, train_y.shape) # (23171,) (23171, 199)

    return train_dense_game, train_dense_players, train_cat_game, train_cat_players, num_classes_cat, train_y, train_y_199


def get_train_tree_data():
    path = 'cache_tree_train.csv'

    if os.path.exists(path):
        train_x_y = pd.read_csv(path)
        print("load train tree data from disk with shape: ", train_x_y.shape)
    else:
        train_dense_game, _, train_cat_game, _, _, train_y, train_y_199 = get_train_NN_data()
        train_x_y = pd.concat([train_dense_game, train_cat_game, train_y], axis=1) # (23171, 71)
        # train_x = pd.concat([train_dense_game, train_cat_game], axis=1, ignore_index=True) # (23171, 71)
        # train_x = pd.merge(train_dense_game, train_cat_game, how='left', on='PlayId')
        train_x_y.to_csv(path, index=False)

    return train_x_y

if __name__ == '__main__':
    init_setting()

    train_x, train_y = get_train_tree_data()

    losses = []
    models = []
    for k in range(1):
        kfold = KFold(5, random_state=42 + k, shuffle=True)
        for k_fold, (tr_inds, val_inds) in enumerate(kfold.split(train_y)):
            print("-----------")
            print("-----------")
            # model, loss = model_NN.train_and_get_model_NN(train_dense_game.value, train_dense_players, train_cat_game.value, train_cat_players,
            #                         train_y_raw, train_y, num_classes_cat, tr_inds, val_inds, 32, 20)
            model, loss = model_NN.lightGBM(train_x, train_y, tr_inds, val_inds)
            models.append(model)
            print(k_fold, loss)
            losses.append(loss)
    print("-------")
    print(losses)
    print(np.mean(losses))