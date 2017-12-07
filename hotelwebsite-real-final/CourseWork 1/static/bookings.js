window.onload = function() {
    var day = today.getDate();

     if (day < 10){
            day = '0' + day
        }

    var month = today.getMonth()+1;

     if (month < 10){
            month = '0' + month
        }

    var year = today.getFullYear();

    var today = new Date();
    today = year + '-' + month + '-' + day;
    $("#ad").attr("min", today);
 }

function arrivalConstraint(){
    $("#dd").attr("min", $("#ad").val());
}