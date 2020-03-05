
var time;
// var divHours;
var divMinutes;
var divSeconds;
var action;


function initLocalClock(time,divHours,divMinutes,divSeconds) {
    this.time=time
    // this.divHours = divHours;
    this.divMinutes = divMinutes;
    this.divSeconds = divSeconds;

    
    setTimeout(updateTime,0);
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