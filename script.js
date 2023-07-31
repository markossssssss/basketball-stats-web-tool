let editedPlayer = null;
let teamAName = "Team A";
let teamBName = "Team B";
const eventTypes = {
  "3分球出手": ["进球", "不进"],
  "2分球出手": ["进球", "不进"],
  "罚球出手": ["进球", "不进"],
  "犯规": ["普通犯规未犯满", "普通犯规犯满", "投篮犯规", "进攻犯规", "技术犯规", "违体犯规进攻", "违体犯规防守"],
  "失误": ["违例", "出界"],
  "篮板": ["前场", "后场"],
  "助攻": ["2分","3分"],
  "盖帽": ["2分","3分"],
  "抢断": [],
  "换人": []
};
const eventTypesWithTarget = ["犯规", "助攻", "抢断", "盖帽", "换人"]

// 获取视频文件输入框和视频播放器
const videoFileInput = document.getElementById("videoFileInput");
const videoPlayer = document.getElementById("videoPlayer");
const quarterButtons = document.querySelectorAll(".quarter-selection button");
quarterButtons[0].classList.add("active");
const quarterTimer = document.getElementById("quarterTimer");

// 视频播放器状态
let isPlaying = false;
let timerActive = false;
let startTime = 0;
let currentQuarter = 1;
let currentQuarterStartTime = 0;

let switchPlayerCount = 0;
let switchPlayerTeamName = "";
let switchPlayerRow = 0;

let startingLineupConfirmed = false;

const teamAPlayers = [
  { name: "A1", jerseyNumber: 11, position: "G" },
  { name: "A2", jerseyNumber: 22, position: "F" },
  { name: "A3", jerseyNumber: 33, position: "C" },
  { name: "A4", jerseyNumber: 44, position: "F/C" },
  { name: "A5", jerseyNumber: 55, position: "C" },
  { name: "A6", jerseyNumber: 66, position: "G" },
  { name: "A7", jerseyNumber: 77, position: "G" },
  { name: "A8", jerseyNumber: 88, position: "G/F" },
  { name: "A9", jerseyNumber: 99, position: "F" }
];

const teamBPlayers = [
  { name: "B1", jerseyNumber: 11, position: "G" },
  { name: "B2", jerseyNumber: 22, position: "F" },
  { name: "B3", jerseyNumber: 33, position: "C" },
  { name: "B4", jerseyNumber: 44, position: "F" },
  { name: "B5", jerseyNumber: 55, position: "G" },
  { name: "B6", jerseyNumber: 66, position: "F/C" },
  { name: "B7", jerseyNumber: 77, position: "F" },
  { name: "B8", jerseyNumber: 88, position: "G" }
];

let teamAPlayersList = [...teamAPlayers]; // Create a copy of the original player list for Team A
let teamBPlayersList = [...teamBPlayers]; // Create a copy of the original player list for Team B


window.onload = function () {
  populatePlayersTable("teamATable", teamAPlayersList);
  populatePlayersTable("teamBTable", teamBPlayersList);
  populateEventTypes("event");
  populatePlayersDropdown();
  populateEventInfoDropdown();

  // 给球队名字输入框添加事件监听器
  document.getElementById("teamNameInputA").addEventListener("input", function () {
    updateTeamName(this.value, teamAName); // 更新球队名字
  });

  // 给球队名字输入框添加事件监听器
  document.getElementById("teamNameInputB").addEventListener("input", function () {
    updateTeamName(this.value, teamBName); // 更新球队名字
  });

  // 更新 populatePlayersDropdown 函数的调用
  document.getElementById("team").addEventListener("change", function () {
    populatePlayersDropdown();
    populateObjectPlayersDropdown(this.value);
  });

  document.getElementById("playerName").addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      addPlayer();
    }
  });

  document.getElementById("playerJersey").addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      addPlayer();
    }
  });

  document.getElementById("playerPosition").addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      addPlayer();
    }
  });

  document.getElementById("event").addEventListener("change", function () {
    populateEventInfoDropdown();
    const selectedTeam = document.getElementById("team").value;
    populateObjectPlayersDropdown(selectedTeam);
  });

//   const addPlayerButton = document.getElementById("addPlayerButton");
//   addPlayerButton.addEventListener("click", addPlayer);

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
  const jerseyCell = row.insertCell();
  const positionCell = row.insertCell();
  const isOnCourtCell = row.insertCell();
  const actionsCell = row.insertCell();

  nameCell.innerText = player.name;
  jerseyCell.innerText = player.jerseyNumber;
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

function updateTeamName(newTeamName, team) {
  console.log("137-----", teamAName, teamBName)
  console.log(newTeamName, team)

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
  const jerseyInput = document.getElementById("playerJersey");
  const positionSelect = document.getElementById("playerPosition");

  console.log("281-----", teamName)
  const playerName = nameInput.value;
  const jerseyNumber = jerseyInput.value;
  const playerPosition = positionSelect.value;

  const player = {
    name: playerName,
    jerseyNumber: jerseyNumber,
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

  nameInput.value = "";
  jerseyInput.value = "";
  positionSelect.value = "";
}

function editPlayer(teamName, rowIndex) {
  console.log("196-------", teamName, rowIndex, teamAName, teamBName)
  const tableId = teamName === teamAName ? "teamATable" : "teamBTable";
  const table = document.getElementById(tableId);
  const row = table.rows[rowIndex + 1];
  const name = row.cells[0].innerText;
  const jersey = row.cells[1].innerText;
  const position = row.cells[2].innerText;
  console.log("203------", table)

  const nameInput = document.getElementById("playerName");
  const jerseyInput = document.getElementById("playerJersey");
  const positionInput = document.getElementById("playerPosition");

  nameInput.value = name;
  jerseyInput.value = jersey;
  positionInput.value = position;

  // 设置当前编辑的球员信息
  editedPlayer = {
    name: name,
    jerseyNumber: jersey,
    position: position,
    teamName: teamName, // 正确获取队伍名称
    rowIndex: rowIndex
  };
}

function saveEdit() {
  if (!editedPlayer) return;

  const nameInput = document.getElementById("playerName");
  const jerseyInput = document.getElementById("playerJersey");
  const positionInput = document.getElementById("playerPosition");

  const playerName = nameInput.value;
  const jerseyNumber = jerseyInput.value;
  const playerPosition = positionInput.value;

  const updatedPlayer = {
    name: playerName,
    jerseyNumber: jerseyNumber,
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
  jerseyInput.value = "";
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
        playerList[switchPlayerRow] = playerList[rowIndex];
        playerList[rowIndex] = temp;
        populatePlayersTable(tableId, playerList); // Update the table

        populatePlayersDropdown();
        populateObjectPlayersDropdown(document.getElementById("team").value);
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

  const table = document.getElementById("eventTable");
  const row = table.insertRow();
  row.insertCell().innerText = team;
  row.insertCell().innerText = player;
  row.insertCell().innerText = formattedTime;
  row.insertCell().innerText = eventType;
  row.insertCell().innerText = eventInfo;
  row.insertCell().innerText = eventTypesWithTarget.includes(eventType) ? objectPlayer : "";
  const deleteButton = document.createElement("button");
  deleteButton.innerText = "Delete";
  deleteButton.addEventListener("click", function () {
    deleteEvent(this);
  });

  row.insertCell().appendChild(deleteButton);
}

function deleteEvent(deleteButton) {
  const row = deleteButton.parentNode.parentNode;
  const table = document.getElementById("eventTable");
  table.deleteRow(row.rowIndex);
}

function confirmStartingLineup() {
  const startTime = "1 - 0 : 00";
  const teamAStartingPlayers = teamAPlayersList.slice(0, 5);
  const teamBStartingPlayers = teamBPlayersList.slice(0, 5);

  const table = document.getElementById("eventTable");

  // 添加 Team A 首发出场事件
  teamAStartingPlayers.forEach(player => {
    _addEvent(table, teamAName, "", startTime, "换人", "", player.name);
  });

  // 添加 Team B 首发出场事件
  teamBStartingPlayers.forEach(player => {
    _addEvent(table, teamBName, "", startTime, "换人", "", player.name);
  });
}

function _addEvent(table, teamName, playerName, startTime, eventType, eventInfo, objectPlayer) {

    const row = table.insertRow();
    row.insertCell().innerText = teamName;
    row.insertCell().innerText = playerName;
    row.insertCell().innerText = startTime;
    row.insertCell().innerText = eventType;
    row.insertCell().innerText = eventInfo;
    row.insertCell().innerText = eventTypesWithTarget.includes(eventType) ? objectPlayer : "";
    const deleteButton = document.createElement("button");
    deleteButton.innerText = "Delete";
    deleteButton.addEventListener("click", function () {
    deleteEvent(this);
  });

  row.insertCell().appendChild(deleteButton);
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
  if (videoFileInput.files.length > 0) {
    const file = videoFileInput.files[0];
    if (file.type.startsWith("video/")) {
      const objectURL = URL.createObjectURL(file);
      videoPlayer.src = objectURL;
      videoPlayer.currentTime = startTime;
      currentQuarterStartTime = startTime;
    //   updateQuarterTimer();
      videoPlayer.play();
    } else {
      alert("请选择一个视频文件！");
    }
  }
  videoPlayer.focus();
}

// 处理视频播放
function handlePlay() {
  isPlaying = true;
  updateTime()
}

// 处理视频暂停
function handlePause() {
  isPlaying = false;
  console.log("1111111")
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
  quarterButtons[quarter - 1].classList.add("active");
//   updateTime();
  videoPlayer.focus();
}

// 开始计时按钮
function startTimer() {
  currentQuarterStartTime = videoPlayer.currentTime
  timerActive = true
  if (currentQuarter === 1) {
      startTime = videoPlayer.currentTime
  }
  updateTime();
  videoPlayer.focus();
}

function onInputFileChange() {
    console.log("fuck")
}
