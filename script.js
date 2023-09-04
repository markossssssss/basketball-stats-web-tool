// 配置

const eventTypes = {
  "3分球出手": ["不进", "进球", "球进加罚"],
  "2分球出手": ["不进", "进球", "球进加罚"],
  "罚球出手": ["进球", "不进"],
  "犯规": ["普通犯规未犯满", "普通犯规犯满", "投篮犯规", "进攻犯规", "技术犯规", "违体犯规进攻", "违体犯规防守"],
  "失误": ["违例", "出界"],
  "篮板": ["后场", "前场"],
  "助攻": ["2分","3分"],
  "盖帽": ["2分","3分"],
  "抢断": [],
  "换人": []
};
const eventTypeNames = ["2分球出手", "3分球出手", "罚球出手", "助攻", "抢断", "犯规", "失误", "换人", "盖帽", "篮板"];
const eventTypesWithTarget = ["犯规", "助攻", "抢断", "盖帽", "换人", "计时开始"];

const teamAPlayersTemplate = [
  { name: "13#队员1", position: "G" },
  { name: "14#队员2", position: "F" },
  { name: "77#队员3", position: "C" },
  { name: "91#队员4", position: "F/C" },
  { name: "35#队员5", position: "C" },
  { name: "19#队员6", position: "G" },
  { name: "20#队员7", position: "G/F" }
];

const teamBPlayersTemplate = [
  { name: "41#队员1", position: "G" },
  { name: "56#队员2", position: "F" },
  { name: "78#队员3", position: "C" },
  { name: "97#队员4", position: "F" },
  { name: "34#队员5", position: "G" },
  { name: "33#队员6", position: "F/C" },
  { name: "12#队员7", position: "F" }
];

// 页面元素
var overlay1 = document.getElementById("overlay1");
var overlay2 = document.getElementById("overlay2");
var overlay3 = document.getElementById("overlay3");
const videoFileInput = document.getElementById("videoFileInput");
const videoPlayer = document.getElementById("videoPlayer");
const quarterButtons = document.querySelectorAll(".quarter-selection button");
quarterButtons[1].classList.add("active");
const quarterTimer = document.getElementById("quarterTimer");
const eventButtons = document.querySelectorAll('.button-container button');
const leftButtons = document.querySelectorAll('.left-button-container button');
const rightButtons = document.querySelectorAll('.right-button-container button');
const centeredButtons = document.querySelectorAll('.center-button-container button');
const infoButtons = document.querySelectorAll('.info-button-container button');
const highlightButtons = document.querySelectorAll('.highlight-button-container button');





// 全局数据变量

let teamAName = "Team A";
let teamBName = "Team B";
let gameID = "";
let gameDate = "";
let teamAPlayersList = [...teamAPlayersTemplate]; 
let teamBPlayersList = [...teamBPlayersTemplate]; 
let events = [];
let currentQuarter = 1;
let currentQuarterStartTime = 0;


// 全局临时记录变量

let editedPlayer = null;
let rostersConfirmed = false;
let isPlaying = false;
let timerActive = false;

let switchPlayerCount = 0;
let switchPlayerTeamName = "";
let switchPlayerRow = 0;


buttonsConcealedFlag = false;

let playerButtonSelectedFlag = false;
let eventButtonSelectedFlag = false;
let objectButtonSelectedFlag = false;
let infoButtonSelectedFlag = false;

let event_team = "";
let event_player = "";
let event_type = "";
let event_time = "";
let event_info = "";
let event_object = "";

let lastButtonId = "";

let isFastForward = false;
let isFastRewind = false;



window.onload = function () {
  openModal1();
  populatePlayersTable("teamATable", teamAPlayersList);
  populatePlayersTable("teamBTable", teamBPlayersList);
  populateEventTypes("event");
  populatePlayersDropdown();
  populateEventInfoDropdown();
  initCenteredButtons();


  // 更新 populatePlayersDropdown 函数的调用
  document.getElementById("team").addEventListener("change", function () {
    populatePlayersDropdown();
    populateObjectPlayersDropdown(this.value);
  });


  document.addEventListener("keyup", function(event) {
    if (event.keyCode === 39) {
      event.preventDefault();
      event.stopPropagation();
      stopFastForward();
    }
    if (event.keyCode === 37) {
      event.preventDefault();
      event.stopPropagation();
      stopFastRewind();
    }
  });
  
  document.addEventListener("keydown", function(event) {
      // "Esc"键
    if (rostersConfirmed) {
      if (event.keyCode === 27) {
      event.preventDefault();
      event.stopPropagation();
      initCenteredButtons()
    }
    // Tab
    if (event.keyCode === 9) {
      event.preventDefault();
      event.stopPropagation();
      centeredButtonClicked(lastButtonId, true)
    }
    // 回车键
    if (event.keyCode === 13) {
      event.preventDefault();
      addEventFromButtons()
    }
    // 空格
    if (event.keyCode === 32) {
      event.preventDefault();
      if (isPlaying) {
          console.log(121212)
          handlePause()
      }
      else {
          console.log(222222222)
          handlePlay()
      }
    }
    // 右方向键
    if (event.keyCode === 39) {
      event.preventDefault();
      event.stopPropagation();
      startFastForward();
    }
    // 左方向键
    if (event.keyCode === 37) {
      event.preventDefault();
      event.stopPropagation();
      startFastRewind();
    }
    // Q
    if (event.keyCode === 81) {
      centeredButtonClicked("leftButton1")
    }
    // W
    if (event.keyCode === 87) {
      centeredButtonClicked("leftButton2")
    }
    // A
    if (event.keyCode === 65) {
      centeredButtonClicked("leftButton3")
    }
    // S
    if (event.keyCode === 83) {
      centeredButtonClicked("leftButton4")
    }
    //D
    if (event.keyCode === 68) {
      centeredButtonClicked("leftButton5")
    }
    //I
    if (event.keyCode === 73) {
      centeredButtonClicked("rightButton1")
    }
    // O
    if (event.keyCode === 79) {
      centeredButtonClicked("rightButton2")
    }
    // J
    if (event.keyCode === 74) {
      centeredButtonClicked("rightButton3")
    }
    // K
    if (event.keyCode === 75) {
      centeredButtonClicked("rightButton4")
    }
    // L
    if (event.keyCode === 76) {
      centeredButtonClicked("rightButton5")
    }
    if (event.keyCode === 49) {
      centeredButtonClicked("centeredButton1")
    }
    if (event.keyCode === 50) {
      centeredButtonClicked("centeredButton2")
    }
    if (event.keyCode === 51) {
      centeredButtonClicked("centeredButton3")
    }
    if (event.keyCode === 52) {
      centeredButtonClicked("centeredButton4")
    }
    if (event.keyCode === 53) {
      centeredButtonClicked("centeredButton5")
    }
    if (event.keyCode === 54) {
      centeredButtonClicked("centeredButton6")
    }
    if (event.keyCode === 55) {
      centeredButtonClicked("centeredButton7")
    }
    if (event.keyCode === 56) {
      centeredButtonClicked("centeredButton8")
    }
    if (event.keyCode === 57) {
      centeredButtonClicked("centeredButton9")
    }
    if (event.keyCode === 48) {
      centeredButtonClicked("centeredButton0")
    }
    if (event.keyCode === 189) {
      centeredButtonClicked("highlightButton1")
    }
    if (event.keyCode === 18) {
      concealButtons()
    }
    }
    
    
    });
    

  document.getElementById("event").addEventListener("change", function () {
    populateEventInfoDropdown();
    const selectedTeam = document.getElementById("team").value;
    populateObjectPlayersDropdown(selectedTeam);
  });


  // 更新 saveEdit 函数的调用
  document.getElementById("saveEditButton").addEventListener("click", saveEdit);
  
  
  populateEventTeamDropdowns();
  videoPlayer.setAttribute("tabindex", "0");
  videoPlayer.focus();
  // 添加视频播放器事件监听
  videoPlayer.addEventListener("play", handlePlay);
  videoPlayer.addEventListener("pause", handlePause);
  videoPlayer.addEventListener("timeupdate", updateTime);

};

function saveDataToLocalStorage() {
  // 将球员名单和事件列表转换为JSON字符串
  const playerAListJSON = JSON.stringify(teamAPlayersList);
  const playerBListJSON = JSON.stringify(teamBPlayersList);
  const eventsListJSON = JSON.stringify(events);
  
  // 使用localStorage保存数据
  localStorage.setItem(gameID, 1);
  localStorage.setItem(`${gameID}_playersA`, playerAListJSON);
  localStorage.setItem(`${gameID}_playersB`, playerBListJSON);
  localStorage.setItem(`${gameID}_events`, eventsListJSON);
  localStorage.setItem(`${gameID}_quarter`, currentQuarter);
  localStorage.setItem(`${gameID}_quarterStart`, currentQuarterStartTime);
}

function loadDataFromLocalStorage() {
  rostersConfirmed = true
  const playerAListJSON = localStorage.getItem(`${gameID}_playersA`);
  const playerBListJSON = localStorage.getItem(`${gameID}_playersB`);
  const eventsListJSON = localStorage.getItem(`${gameID}_events`);
  currentQuarter = localStorage.getItem(`${gameID}_quarter`);
  currentQuarterStartTime = localStorage.getItem(`${gameID}_quarterStart`);
  selectQuarter(currentQuarter)
  if (playerAListJSON && playerBListJSON) {
    teamAPlayersList = JSON.parse(playerAListJSON);
    teamBPlayersList = JSON.parse(playerBListJSON);
    populatePlayersTable("teamATable", teamAPlayersList)
    populatePlayersTable("teamBTable", teamBPlayersList)
    populatePlayersDropdown();
    populateObjectPlayersDropdown(document.getElementById("team").value);
    populateEventTeamDropdowns();
    initCenteredButtons();
  }
  if (eventsListJSON) {
    events = JSON.parse(eventsListJSON);
    events.forEach(event => _addEvent(event[0], event[1], event[2], event[3], event[4], event[5], save=false));
  }
}

function openModal1() {
  overlay1.style.display = "flex"; // 显示遮罩层
}

function openModal2() {
  overlay2.style.display = "flex"; // 显示遮罩层
}

function openModal3() {
  overlay3.style.display = "flex"; // 显示遮罩层
}

function newGame() {
  overlay2.style.display = "none";
  overlay3.style.display = "none";
  console.log("new game start")
}

function loadGame() {
  overlay3.style.display = "none";
  loadDataFromLocalStorage()
  console.log("load game start")
  
}

function gameInfo() {
            // 获取输入的信息
    var team1Name = document.getElementById("team1").value;
    var team2Name = document.getElementById("team2").value;
    var matchDate = document.getElementById("matchDate").value;
    
    gameDate = matchDate
    gameID = `${team1Name}_${team2Name}_${matchDate}`
    updateTeamNames(team1Name, team2Name)

    // 隐藏模态框
    overlay1.style.display = "none";
    
    if (localStorage.getItem(gameID) == null) {
        openModal2();
    }
    else {
        openModal3();
    }

    // 在这里可以执行你的进一步操作，比如更新页面内容等
}

function startFastForward() {
      if (videoPlayer) {
        isFastForward = true;
        videoPlayer.playbackRate = 2;
}
}

function stopFastForward() {
      if (videoPlayer && isFastForward) {
        isFastForward = false;
        videoPlayer.playbackRate = 1;
      }
}

function startFastRewind() {
      if (videoPlayer) {
        isFastRewind = true;
        videoPlayer.playbackRate = -2;
}
}

function stopFastRewind() {
      if (videoPlayer && isFastRewind) {
        isFastRewind = false;
        videoPlayer.playbackRate = 1;
      }
}

function centeredButtonClicked(buttonId, tab = false) {
    console.log("111")
    if (!rostersConfirmed) {
      window.alert("请先确认名单");
      return;
    }

    if (!timerActive) {
      window.alert("请先开始计时");
      return;
    }
    let index = Number(buttonId.split("Button")[1]) - 1;
    if (tab && !infoButtonSelectedFlag) {
        return;
    }
    else if (tab) {
      console.log("shit")
      if (eventTypes[event_type].length == 0) {
          return;
      }
      index += 1;
      index %= eventTypes[event_type].length;
    }
    
    if (buttonId.charAt(0) == "l") {
      if (!playerButtonSelectedFlag || !eventButtonSelectedFlag) {
        buttonActiveControl(leftButtons, index, "active1");
        playerButtonSelectedFlag = true;
        event_player = teamAPlayersList[index].name;
        event_team = teamAName;
        // if (eventButtonSelectedFlag) {
        //     showInfoButtons(event_type)
        // }
      }
      else if (!objectButtonSelectedFlag && eventTypesWithTarget.includes(event_type)) {
        if ((["抢断", "盖帽", "犯规"].includes(event_type) && event_team == teamBName) || (["助攻", "换人"].includes(event_type) && event_team == teamAName)) {
          buttonActiveControl(leftButtons, index, "active3");
          objectButtonSelectedFlag = true;
          event_object = teamAPlayersList[index].name  
        }
      }
      
    }
    else if (buttonId.charAt(0) == "r") {
      if (!playerButtonSelectedFlag || !eventButtonSelectedFlag) {
        buttonActiveControl(rightButtons, index, "active1");
        playerButtonSelectedFlag = true;
        event_player = teamBPlayersList[index].name;
        event_team = teamBName;
        // if (eventButtonSelectedFlag) {
        //     showInfoButtons(event_type)
        // }
      }
      else if (!objectButtonSelectedFlag && eventTypesWithTarget.includes(event_type)) {
        if ((["抢断", "盖帽", "犯规"].includes(event_type) && event_team == teamAName) || (["助攻", "换人"].includes(event_type) && event_team == teamBName)) {
          buttonActiveControl(rightButtons, index, "active3");
          objectButtonSelectedFlag = true;
          event_object = teamBPlayersList[index].name  
        }
      }
    }
    else if (buttonId.charAt(0) == "c") {
      if (!eventButtonSelectedFlag || !playerButtonSelectedFlag) {
        buttonActiveControl(centeredButtons, index, "active2");
        eventButtonSelectedFlag = true;
        event_type = eventTypeNames[index]
        showInfoButtons(event_type)
      }
    }
    else if (buttonId.charAt(0) == "i") {
        lastButtonId = `infoButton${index+1}`;
        buttonActiveControl(infoButtons, index, "active4");
        event_info = eventTypes[event_type][index]
        infoButtonSelectedFlag = true;
    }
    else if (buttonId.charAt(0) == "h") {
        info = "bad"
        addHighlight(info)
    }
    console.log(event_team, event_player, event_type, event_info, event_object)
    
    
    // videoPlayer.focus();
}

function buttonActiveControl(buttons, index, active_id) {
  buttons.forEach(button => button.classList.remove(active_id));
  buttons[index].classList.add(active_id);
}

function addEventFromButtons() {
    result = eventChecker()
    console.log(result)
    if (result) {
      if (event_info == "球进加罚") {
        event_info = "进球";
        addEventFromGlobal();
        initCenteredButtons();
        centeredButtonClicked("centeredButton3") // 罚球事件
      }
      else if (event_info == "不进") {
        addEventFromGlobal();
        initCenteredButtons();
        centeredButtonClicked("centeredButton10") // 篮板事件
      }
      else {
        addEventFromGlobal();
        initCenteredButtons();
      }
    }
}

function showInfoButtons(event_type) {
    for (var i = 0; i < 7; i++) {
      var infoButton = document.getElementById('info' + 'Button' + (i + 1));
      infoButton.style = "display:none;";
    }
    if (event_type === "2分") {
      event_type = "2分球出手"
    }
    else if (event_type === "3分") {
      event_type = "3分球出手"
    }
    else if (event_type === "罚球") {
      event_type = "罚球出手"
    }
    infos = eventTypes[event_type]
    for (var i = 0; i < infos.length; i++) {
      var infoButton = document.getElementById('info' + 'Button' + (i + 1));
      infoButton.style = "display:block;"
      infoButton.innerText = infos[i];
    }
    if (infos.length) {
      infoButtons.forEach(button => button.classList.remove("active4"));
      infoButtons[0].classList.add("active4");
      lastButtonId = "infoButton1";
      event_info = infos[0];
      infoButtonSelectedFlag = true;
    }
    
}

function eventChecker() {
    if (!playerButtonSelectedFlag) {
        window.alert("请选择球员");
        return 0;
    }
    if (!eventButtonSelectedFlag) {
        window.alert("请选择事件");
        return 0;
    }
    if (!objectButtonSelectedFlag === "" && eventTypesWithTarget.includes(event_type)) {
        window.alert("请选择对象球员");
        return 0;
    }
    return 1
}


function initCenteredButtons() {
  playerButtonSelectedFlag = false;
  eventButtonSelectedFlag = false;
  objectButtonSelectedFlag = false;
  infoButtonSelectedFlag = false;
  event_team = "";
  event_player = "";
  event_time = "";
  event_info = "";
  event_object = "";
  lastButtonId = "";
  eventButtons.forEach(button => button.classList.remove("active1"));
  eventButtons.forEach(button => button.classList.remove("active2"));
  eventButtons.forEach(button => button.classList.remove("active3"));
  eventButtons.forEach(button => button.classList.remove("active4"));
  for (var i = 0; i < 12; i++) {
    var leftPlayerButton = document.getElementById('left' + 'Button' + (i + 1));
    var rightPlayerButton = document.getElementById('right' + 'Button' + (i + 1));
    if (teamAPlayersList[i]) {
      if (i < 5) {
        leftPlayerButton.innerText = teamAPlayersList[i].name;
        leftPlayerButton.style = "display:block;"
    //   leftPlayerButton.style.backgroundColor = 'navy'   
      }
      else {
        leftPlayerButton.innerText = teamAPlayersList[i].name;
        leftPlayerButton.style = "display:none;"
      }
    } 
    else {
        leftPlayerButton.style = "display:none;"
    }
    if (teamBPlayersList[i]) {
      if (i < 5) {
        rightPlayerButton.innerText = teamBPlayersList[i].name;
        rightPlayerButton.style = "display:block;"
    //   leftPlayerButton.style.backgroundColor = 'navy'   
      }
      else {
        rightPlayerButton.innerText = teamBPlayersList[i].name;
        rightPlayerButton.style = "display:none;"
      }
    } 
    else {
        rightPlayerButton.style = "display:none;"
    }
  }
  
  for (var i = 0; i < 10; i++) {
    var centeredPlayerButton = document.getElementById('centered' + 'Button' + (i + 1));
    centeredPlayerButton.style = "display:block;";
  }
  for (var i = 0; i < 7; i++) {
    var infoButton = document.getElementById('info' + 'Button' + (i + 1));
    infoButton.style = "display:none;";
  }
}


function concealButtons() {
  if (!buttonsConcealedFlag) {
    buttonsConcealedFlag = true;
    for (var i = 0; i < 12; i++) {
      var leftPlayerButton = document.getElementById('left' + 'Button' + (i + 1));
      var rightPlayerButton = document.getElementById('right' + 'Button' + (i + 1));
      leftPlayerButton.style = "display:none;"
      rightPlayerButton.style = "display:none;"
    }
    for (var i = 0; i < 10; i++) {
      var centeredButton = document.getElementById('centered' + 'Button' + (i + 1));
      centeredButton.style = "display:none;"
    }
    for (var i = 0; i < 7; i++) {
      var infoButton = document.getElementById('info' + 'Button' + (i + 1));
      infoButton.style = "display:none;"
    }
  }
  else {
    initCenteredButtons()
    buttonsConcealedFlag = false;
  }
}


function createPlayerRow(player, tableId, rowIndex) {
  const table = document.getElementById(tableId);

  // Check if the table exists
  if (!table) {
    console.error(`Table ${tableId} not found.`);
    return;
  }

  const row = table.insertRow();
  row.setAttribute("id", `${tableId}-row-${rowIndex}`);
  row.setAttribute("data-team", tableId === "teamATable" ? teamAName : teamBName);

  const nameCell = row.insertCell();
  const positionCell = row.insertCell();
  const isOnCourtCell = row.insertCell();
  const actionsCell = row.insertCell();

  nameCell.innerText = player.name;
  positionCell.innerText = player.position;
  isOnCourtCell.innerText = rowIndex < 5 ? "是" : "";
  actionsCell.innerHTML = `<button onclick="editPlayer('${tableId === 'teamATable' ? teamAName : teamBName}', ${rowIndex})">编辑</button>
                           <button onclick="deletePlayer('${tableId === 'teamATable' ? teamAName : teamBName}', ${rowIndex})">删除</button>
                           <button onclick="switchPlayer('${tableId === 'teamATable' ? teamAName : teamBName}', ${rowIndex})">换人</button>`;
  console.log("97----", tableId, teamAName, teamBName)
}

function populateEventInfoDropdown() {
  const eventType = document.getElementById("event").value;
  const eventInfoSelect = document.getElementById("eventInfo");
  eventInfoSelect.innerHTML = "";

  const eventInfoOptions = eventTypes[eventType];
  eventInfoOptions.forEach(option => {
    const eventInfoOption = document.createElement("option");
    eventInfoOption.value = option;
    eventInfoOption.innerText = option;
    eventInfoSelect.appendChild(eventInfoOption);
  });
}


function populatePlayersTable(tableId, players) {
  const table = document.getElementById(tableId);

  // Clear all rows from the table except the header row
  while (table.rows.length > 1) {
    table.deleteRow(1);
  }

  players.forEach((player, index) => {
    createPlayerRow(player, tableId, index);
  });
}

function populateEventTypes(selectId) {
  const select = document.getElementById(selectId);
  for (const eventType in eventTypes) {
    const option = document.createElement("option");
    option.value = eventType;
    option.innerText = eventType;
    select.appendChild(option);
  }
}

function populatePlayersDropdown(oncourt=2) {
    // oncourt === 0:替补 oncourt === 1:首发 oncourt === 2:全体
  const teamSelect = document.getElementById("team");
  const playerSelect = document.getElementById("player");
  const selectedTeam = teamSelect.value;
  
  let playersList;
  if (selectedTeam === teamAName) {
    playersList = teamAPlayersList;
  } else if (selectedTeam === teamBName) {
    playersList = teamBPlayersList;
  }

  // 清空 playerSelect 元素中的选项
  playerSelect.innerHTML = "";
  
  // 根据选中的球队更新球员列表
  if (playersList) {
    if (oncourt === 2) {
      for (i in playersList) {
        console.log(playersList[i])
        const option = document.createElement("option");
        option.value = playersList[i].name;
        option.innerText = playersList[i].name;
        playerSelect.appendChild(option);
      }
    }
    else if (oncourt === 1) {
      let count = 0
      for (player in playersList) {
        if (count >= 5) {break}
        const option = document.createElement("option");
        option.value = player.name;
        option.innerText = player.name;
        playerSelect.appendChild(option);
        count += 1;
      }
    }
    else if (oncourt === 0) {
      let count = 0
      for (player in playersList) {
        if (count < 5) {
            count += 1;
            continue
        }
        const option = document.createElement("option");
        option.value = player.name;
        option.innerText = player.name;
        playerSelect.appendChild(option);
        count += 1;
      }
      
    }
  }
}

function updateTeamNames(teamA, teamB) {
  teamAName = teamA;
  teamBName = teamB;
  populatePlayersTable("teamATable", teamAPlayersList)
  populatePlayersTable("teamBTable", teamBPlayersList)
  populatePlayersDropdown();
  populateObjectPlayersDropdown(document.getElementById("team").value);
  populateEventTeamDropdowns();
  document.getElementById('teamAName').textContent = teamA;
  document.getElementById('teamBName').textContent = teamB;
}

function updateTeamName(newTeamName, team) {

  if (team === teamAName) {
    teamAName = newTeamName;
  } else {
    teamBName = newTeamName;
  }
  
  teamPlayersList = newTeamName === teamAName ? teamAPlayersList : teamBPlayersList
  tableId = newTeamName === teamAName ? "teamATable" : "teamBTable"

  populatePlayersTable(tableId, teamPlayersList); // Update the table

  populatePlayersDropdown();
  populateObjectPlayersDropdown(document.getElementById("team").value);

  // 更新添加事件栏的球队名字选项
  populateEventTeamDropdowns();
}


function addPlayer(event) {
  event.preventDefault();
  const teamName = document.getElementById("teamName").value;
  const nameInput = document.getElementById("playerName");
  const positionSelect = document.getElementById("playerPosition");

  console.log("281-----", teamName)
  const playerName = nameInput.value;
  const playerPosition = positionSelect.value;

  const player = {
    name: playerName,
    position: playerPosition
  };

  let playerList;
  if (teamName === teamAName) {
    teamAPlayersList.push(player);
    playerList = teamAPlayersList;
  } else if (teamName === teamBName) {
    teamBPlayersList.push(player);
    playerList = teamBPlayersList;
  }

  const tableId = teamName === teamAName ? "teamATable" : "teamBTable";
  createPlayerRow(player, tableId, playerList.length - 1);

  populatePlayersDropdown();
  populateObjectPlayersDropdown(document.getElementById("team").value);
  initCenteredButtons();

  nameInput.value = "";
  positionSelect.value = "";
}

function editPlayer(teamName, rowIndex) {
  if (rostersConfirmed) {
    window.alert("确认名单后不能编辑球员");
    return
  }
  console.log("196-------", teamName, rowIndex, teamAName, teamBName)
  const tableId = teamName === teamAName ? "teamATable" : "teamBTable";
  const table = document.getElementById(tableId);
  const row = table.rows[rowIndex + 1];
  const name = row.cells[0].innerText;
  const position = row.cells[1].innerText;
  console.log("203------", table)

  const nameInput = document.getElementById("playerName");
  const positionInput = document.getElementById("playerPosition");
  initCenteredButtons();

  nameInput.value = name;
  positionInput.value = position;

  // 设置当前编辑的球员信息
  editedPlayer = {
    name: name,
    position: position,
    teamName: teamName, // 正确获取队伍名称
    rowIndex: rowIndex
  };
}

function saveEdit() {
  if (!editedPlayer) return;

  const nameInput = document.getElementById("playerName");
  const positionInput = document.getElementById("playerPosition");

  const playerName = nameInput.value;
  const playerPosition = positionInput.value;
  initCenteredButtons();

  const updatedPlayer = {
    name: playerName,
    position: playerPosition
  };

  if (editedPlayer.teamName === teamAName) {
  teamAPlayersList[editedPlayer.rowIndex] = updatedPlayer;
  populatePlayersTable("teamATable", teamAPlayersList);
} else if (editedPlayer.teamName === teamBName) {
  teamBPlayersList[editedPlayer.rowIndex] = updatedPlayer;
  populatePlayersTable("teamBTable", teamBPlayersList);
}

  // 清空当前编辑的球员信息
  editedPlayer = null;

  // 清空输入框
  nameInput.value = "";
  positionInput.value = "";
}

function deletePlayer(teamName, rowIndex) {
  const tableId = teamName === teamAName ? "teamATable" : "teamBTable";
  const table = document.getElementById(tableId);
  table.deleteRow(rowIndex+1);

  let playerList;
  if (teamName === teamAName) {
    playerList = teamAPlayersList;
  } else if (teamName === teamBName) {
    playerList = teamBPlayersList;
  }

  if (rowIndex >= 0 && rowIndex < playerList.length) {
    playerList.splice(rowIndex, 1); // Remove the player from the list
  }

  populatePlayersTable(tableId, playerList); // Update the table

  populatePlayersDropdown();
  populateObjectPlayersDropdown(document.getElementById("team").value);
  initCenteredButtons();
}

function switchPlayer(teamName, rowIndex) {
    console.log(switchPlayerCount)
    if (switchPlayerCount === 0) {
        switchPlayerTeamName = teamName;
        switchPlayerCount += 1;
        switchPlayerRow = rowIndex;
    }
    else if (teamName === switchPlayerTeamName && rowIndex === switchPlayerRow) {
        return
    }
    else if (teamName === switchPlayerTeamName) {
        switchPlayerCount = 0;
        if (teamName === teamAName) {
            playerList = teamAPlayersList;
            tableId = "teamATable"
        } else if (teamName === teamBName) {
            playerList = teamBPlayersList;
            tableId = "teamBTable"
        }
        let temp = playerList[switchPlayerRow];
        let player1 = playerList[Math.min(switchPlayerRow, rowIndex)].name
        let player2 = playerList[Math.max(rowIndex, switchPlayerRow)].name
        if ((rostersConfirmed) && (Math.min(switchPlayerRow, rowIndex) <= 4) && ((Math.max(switchPlayerRow, rowIndex) >= 5))) {
          addSwitchEvent(teamName, player1, player2);   
        }
        playerList[switchPlayerRow] = playerList[rowIndex];
        playerList[rowIndex] = temp;
        populatePlayersTable(tableId, playerList); // Update the table

        populatePlayersDropdown();
        populateObjectPlayersDropdown(document.getElementById("team").value);
        initCenteredButtons();
    }
    else {
        switchPlayerCount === 0;
    }
    console.log(switchPlayerCount)
}


function populateObjectPlayersDropdown(selectedTeam) {
  const objectPlayerSelect = document.getElementById("objectPlayer");
  objectPlayerSelect.innerHTML = "";
  
  const teamName = document.getElementById("event").value;
  const eventType = document.getElementById("event").value;
  const showDropdown = eventTypesWithTarget.includes(eventType);
  const sameTeam = ["助攻", "换人"].includes(eventType)
  if (selectedTeam === teamAName) {
      objectPlayersList = sameTeam ? teamAPlayersList : teamBPlayersList;
  }
  else {
      objectPlayersList = sameTeam ? teamBPlayersList : teamAPlayersList;
  }
  
  console.log(selectedTeam)
  if (showDropdown) {
    objectPlayersList.forEach(player => {
    if (player.name !== document.getElementById("player").value) {
      const option = document.createElement("option");
      option.value = player.name;
      option.innerText = player.name;
      objectPlayerSelect.appendChild(option);
    }
  });
  }
}

function deleteEvent(deleteButton) {
  const row = deleteButton.parentNode.parentNode;
  const table = document.getElementById("eventTable");
  events.splice(row.rowIndex-1,1)
  console.log(events)
  table.deleteRow(row.rowIndex);
}

function confirmStartingLineup() {
  rostersConfirmed = true;
  const startTime = "1 - 0 : 00";
  const teamAStartingPlayers = teamAPlayersList.slice(0, 5);
  const teamBStartingPlayers = teamBPlayersList.slice(0, 5);

  // 添加 Team A 首发出场事件
  teamAStartingPlayers.forEach(player => {
    _addEvent(teamAName, "", startTime, "换人", "", player.name);
  });

  // 添加 Team B 首发出场事件
  teamBStartingPlayers.forEach(player => {
    _addEvent(teamBName, "", startTime, "换人", "", player.name);
  });
}

function addSwitchEvent(team, player1, player2) {
  const eventType = document.getElementById("event").value;
  const eventInfo = document.getElementById("eventInfo").value;
  const quarter = document.getElementById("quarter").value;
  const minutes = document.getElementById("minutes").value;
  const seconds = document.getElementById("seconds").value;

  const formattedTime = `${quarter} - ${minutes} : ${seconds}`;
  _addEvent(team, player1, formattedTime, "换人", "", player2);

}

function addEvent() {
  const team = document.getElementById("team").value;
  const player = document.getElementById("player").value;
  const eventType = document.getElementById("event").value;
  const eventInfo = document.getElementById("eventInfo").value;
  const quarter = document.getElementById("quarter").value;
  const minutes = document.getElementById("minutes").value;
  const seconds = document.getElementById("seconds").value;
  const objectPlayer = document.getElementById("objectPlayer").value;

  const formattedTime = `${quarter} - ${minutes} : ${seconds}`;

  _addEvent(team, player, formattedTime, eventType, eventInfo, objectPlayer);
}

function _addEvent(teamName, playerName, startTime, eventType, eventInfo, objectPlayer, save=true) {
    const table = document.getElementById("eventTable");
    const row = table.insertRow();
    objectPlayer = eventTypesWithTarget.includes(eventType) ? objectPlayer : "";
    row.insertCell().innerText = teamName;
    row.insertCell().innerText = playerName;
    row.insertCell().innerText = startTime;
    row.insertCell().innerText = eventType;
    row.insertCell().innerText = eventInfo;
    row.insertCell().innerText = objectPlayer;
    
    events.push([teamName, playerName, startTime, eventType, eventInfo, objectPlayer])
    if (save) {saveDataToLocalStorage();}
    console.log(events)
    
    const deleteButton = document.createElement("button");
    deleteButton.innerText = "Delete";
    deleteButton.addEventListener("click", function () {
    deleteEvent(this);
  });

  row.insertCell().appendChild(deleteButton);
}

function addEventFromGlobal() {
  const quarter = document.getElementById("quarter").value;
  const minutes = document.getElementById("minutes").value;
  const seconds = document.getElementById("seconds").value;
  const formattedTime = `${quarter} - ${minutes} : ${seconds}`;
    
  _addEvent(event_team, event_player, formattedTime, event_type, event_info, event_object);
}


function addTimerEvent(quarter, quarterStartTime) {
  const startTime = Math.floor(quarterStartTime)
  const formattedTime = `1 - 0 : 0`;
  
  _addEvent("", "", formattedTime, "计时开始", startTime, quarter);
}

function addHighlight(info) {
    const quarter = document.getElementById("quarter").value;
    const minutes = document.getElementById("minutes").value;
    const seconds = document.getElementById("seconds").value;
    const formattedTime = `${quarter} - ${minutes} : ${seconds}`;
    _addEvent("", "", formattedTime, "highlight", info, "");
}


function populateEventTeamDropdowns() {
  const eventTeamDropdowns = document.querySelectorAll(".event-team-dropdown");
  eventTeamDropdowns.forEach(dropdown => {
    dropdown.innerHTML = ""; // 清空下拉菜单

    // 添加 Team A 选项
    const optionA = document.createElement("option");
    optionA.value = teamAName;
    optionA.innerText = teamAName;
    dropdown.appendChild(optionA);

    // 添加 Team B 选项
    const optionB = document.createElement("option");
    optionB.value = teamBName;
    optionB.innerText = teamBName;
    dropdown.appendChild(optionB);
  });
}


function downloadCSV(filename, csvData) {
  const blob = new Blob([csvData], { type: "text/csv;charset=utf-8;" });

  if (navigator.msSaveBlob) {
    // For IE and Edge
    navigator.msSaveBlob(blob, filename);
  } else {
    // For other browsers
    const link = document.createElement("a");
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute("download", filename);
      link.style.visibility = "hidden";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }
}

function exportToCSV() {
  const table = document.getElementById("eventTable");
  let csvData = "Team,Player,Time,Event,Info,Object\n";

  for (let i = 1; i < table.rows.length; i++) {
    for (let j = 0; j < table.rows[i].cells.length-1; j++) {
      if (j === table.rows[i].cells.length-2) {
          csvData += table.rows[i].cells[j].innerText;
      }
      else {
          csvData += table.rows[i].cells[j].innerText + ",";
      }
    }
    csvData += "\n";
  }

  const filename = "basketball_stats.csv";
  downloadCSV(filename, csvData);
}

// 打开本地视频文件
function playSelectedVideo() {
  if (!rostersConfirmed) {
      window.alert("请先确认名单");
      return
  }
  if (videoFileInput.files.length > 0) {
    const file = videoFileInput.files[0];
    if (file.type.startsWith("video/")) {
      const objectURL = URL.createObjectURL(file);
      videoPlayer.src = objectURL;
      videoPlayer.currentTime = 0;
      currentQuarterStartTime = 0;
    //   updateQuarterTimer();
      videoPlayer.play();
    } else {
      alert("请选择一个视频文件！");
    }
  }
  videoPlayer.focus();
  isPlaying = true;
}

// 处理视频播放
function handlePlay() {
  isPlaying = true;
  videoPlayer.play();
  updateTime()
}

// 处理视频暂停
function handlePause() {
  videoPlayer.pause();
  isPlaying = false;
}

// 更新时间
function updateTime() {
  const currentTime = videoPlayer.currentTime;
  if (timerActive) {
    const quarterTime = currentTime - currentQuarterStartTime;
    document.getElementById("currentQuarterTime").innerText = formatTime(quarterTime);
    document.getElementById("quarter").value = currentQuarter;
    document.getElementById("minutes").value = Math.floor(quarterTime/60);
    document.getElementById("seconds").value = Math.floor(quarterTime%60);
  }
}

// 格式化时间为 mm:ss
function formatTime(timeInSeconds) {
  const minutes = Math.floor(timeInSeconds / 60);
  const seconds = Math.floor(timeInSeconds % 60);
  return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
}

// 选择第几节
function selectQuarter(quarter) {
  currentQuarter = quarter;
  quarterButtons.forEach(button => button.classList.remove("active"));
  quarterButtons[quarter].classList.add("active");
//   updateTime();
  videoPlayer.focus();
}

// 开始计时按钮
function startTimer() {
  currentQuarterStartTime = videoPlayer.currentTime
  timerActive = true
  updateTime();
  videoPlayer.focus();
  addTimerEvent(currentQuarter, currentQuarterStartTime)
}

function onInputFileChange() {
    console.log("fuck")
}

function showButtons() {
  const leftButtonsContainer = document.getElementById("leftButtonsContainer");
  const rightButtonsContainer = document.getElementById("rightButtonsContainer");
  leftButtonsContainer.style.display = "flex";
  rightButtonsContainer.style.display = "flex";
}

function hideButtons() {
  const leftButtonsContainer = document.getElementById("leftButtonsContainer");
  const rightButtonsContainer = document.getElementById("rightButtonsContainer");
  leftButtonsContainer.style.display = "none";
  rightButtonsContainer.style.display = "none";
}
