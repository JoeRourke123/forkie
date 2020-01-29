$(document).ready(() => {
   $(".switch").on("click", (e) => {
        e.preventDefault();
        if($(".signin").is(":visible")) {
            $(".signin").hide();
            $(".signup").fadeToggle(1000);
        } else {
            $(".signup").hide();
            $(".signin").fadeToggle(1000);
        }
    });
});