$(function(){

    var dtToday = new Date();
    var day = dtToday.getDate();
    var month = dtToday.getMonth() + 1;
  
    if(month < 10){
      month = '0' + month.toString();
    }
    if(day < 10){
      day = '0' + day.toString();
    }
  
    var year = dtToday.getFullYear();
    var maxDate = year + '-' + month + '-' + day;    
    document.getElementById("previous_data").setAttribute('max' , maxDate) 
  
  });

  // $(function(){
  //   var store = "{{health_sessions.date_of_session}}";
  //   console.log(store)
  //   var newdate = document.getElementById("previous_data").value;
        
  //   if(store === newdate){
  //     alert("Warning!! passcodes must match!!!");
  //     console.log("Warning!! passcodes must match!!!");
  //   }
  //   else{
  //     alert("Sucees");
  //     console.log("Success");

  //   }
  // })

  