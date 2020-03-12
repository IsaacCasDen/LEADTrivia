
var time;
// var divHours;
var divMinutes;
var divSeconds;
var thresholds;
var action;


function initLocalClock(time,thresholds,divHours,divMinutes,divSeconds) {
    this.time=time;
    this.thresholds = thresholds;
    // this.divHours = divHours;
    this.divMinutes = divMinutes;
    this.divSeconds = divSeconds;
    checkThresholds()
    
    setTimeout(updateTime,0);
}
function checkThresholds() {
    for (i in thresholds) {
        t = parseInt(time);
        v = thresholds[i][0];
        if (parseInt(time)<=thresholds[i][0] && thresholds[i][2] === undefined) {
            thresholds[2] = true;
            thresholds[i][1]();
        }
    }
}

// function calcTimeRemaining(datetime) {
//     var value = new Date(datetime);
//     var diff = (value - Date.now())/1000; 
//     return diff;
// }

function updateTime() {
    if (this.time>=0) {
        setTimeout(updateTime,1000);
    } else {
        if (action != undefined) {
            action();
        }
        return;
    }
    for (i in thresholds) {
        if (parseInt(time)==thresholds[i][0] && thresholds[i][2] === undefined) {
            thresholds[2] = true;
            thresholds[i][1]();    
        }
    }
    
    var seconds = parseInt(this.time%60).toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping:false});
    var minutes = parseInt(this.time/60).toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping:false});
    // var hours = parseInt(this.time/3600).toLocaleString('en-US', {minimumIntegerDigits: 2, useGrouping:false});

    // this.divHours.innerText = hours;
    this.divMinutes.innerText = minutes;
    this.divSeconds.innerText = seconds;
    
    this.time--;
}

function setAction(action) {
    this.action = action;
}