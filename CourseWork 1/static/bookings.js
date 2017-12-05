//TODO: Make original help
window.onload = function() {
var today = new Date();
var dd = today.getDate();
var mm = today.getMonth()+1; //January is 0!
var yyyy = today.getFullYear();
 if(dd<10){
        dd='0'+dd
    }
    if(mm<10){
        mm='0'+mm
    }

today = yyyy+'-'+mm+'-'+dd;
$("#ad").attr("min", today);
}

function arrivalConstraint(){
    $("#dd").attr("min", $("#ad").val());
}