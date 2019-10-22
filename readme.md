# EDA

### Data

https://www.kaggle.com/c/nfl-big-data-bowl-2020/data

- `GameId` - a unique game identifier 比赛ID
- `PlayId` - a unique play identifier 一场比赛中所有play的ID（每次play都有可能得分）
- `Team` - home or away 队名
- `X` - player position along the long axis of the field. See figure below.
- `Y` - player position along the short axis of the field. See figure below.
 ![img](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F3258%2F7542d363a19fa3eea77708e6b90bc420%2FFig1.png?generation=1570562067917019&alt=media)
> NFL和NCAA使用的标准球场是一个长360英尺（120码或109.7米）、宽160英尺（53.33码或48.8米）的长方形草坪（有些室内赛会使用仿草地毯），较长的边界称为边线（sideline），较短的边界称为端线（end line）。端线前的标示线称为得分线（goal line），球场每侧端线与得分线之间有一个纵深10码（9.1米）的得分区叫做端区（end zone，也称达阵区），端区的四角各有一个约有1英尺长的橙色长方体标柱（pylon）。两侧得分线相距100码（91.44米），之间的区域也就是比赛区（playing field）。比赛区上距离得分线每5码（4.6米）距离标划一条码线（yard line，或称5码线），每10码标示数字，直到50码线到达中场（midfield）。在球场中间和两侧与边线平行排列划有横向的短标示线，称为码标（hash marks，或称整码线），其中接近边线的码标线称为界内线（inbounds line）。任何球员都必须在码标线上或之间进行发球。
- `S` - speed in yards/second 此时的速度
- `A` - acceleration in yards/second^2 加速度
- `Dis` - distance traveled from prior time point, in yards
- `Orientation` - orientation of player (deg) 运动员此时的朝向
- `Dir` - angle of player motion (deg) 运动的方向
- `NflId` - a unique identifier of the player 运动员ID
- `DisplayName` - player's name 运动员name
- `JerseyNumber` - jersey number 运动员号码
- `Season` - year of the season
- `YardLine` - the yard line of the line of scrimmage 发球的码线
- `Quarter` - game quarter (1-5, 5 == overtime) 比赛所处的时间
- `GameClock` - time on the game clock 
- `PossessionTeam` - team with possession
- `Down` - the down (1-4)
- `Distance` - yards needed for a first down
- `FieldPosition` - which side of the field the play is happening on
- `HomeScoreBeforePlay` - home team score before play started 主队已经获得的比分
- `VisitorScoreBeforePlay` - visitor team score before play started 客队已经获得的比分
- `NflIdRusher` - the `NflId` of the rushing player 进攻方持球选手ID
- `OffenseFormation` - offense formation
- `OffensePersonnel` - offensive team positional grouping 进攻队员
- `DefendersInTheBox` - number of defenders lined up near the line of scrimmage, spanning the width of the offensive line
- `DefensePersonnel` - defensive team positional grouping 防守队员
- `PlayDirection` - direction the play is headed
- `TimeHandoff` - UTC time of the  handoff 传球时间
- `TimeSnap` - UTC time of the snap 发球的时间
- **`Yards` - the yardage gained on the play (you are predicting this)** 得分
- `PlayerHeight` - player height (ft-in)
- `PlayerWeight` - player weight (lbs)
- `PlayerBirthDate` - birth date (mm/dd/yyyy)
- `PlayerCollegeName` - where the player attended college
- `HomeTeamAbbr` - home team abbreviation
- `VisitorTeamAbbr` - visitor team abbreviation
- `Week` - week into the season
- `Stadium` - stadium where the game is being played
- `Location` - city where the game is being player
- `StadiumType` - description of the stadium environment 体育馆类型
- `Turf` - description of the field surface 场地类型
- `GameWeather` - description of the game weather
- `Temperature` - temperature (deg F)
- `Humidity` - humidity 湿度
- `WindSpeed` - wind speed in miles/hour
- `WindDirection` - wind direction