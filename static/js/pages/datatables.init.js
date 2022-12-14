$(document).ready(function () {
    $("#datatable").DataTable(), $("#datatable-buttons").DataTable({
        buttons: ["colvis"],
        stateSave: true,
        paging:false,
        searching: false,
        info:false,
        ordering:false,
        bRetrieve: true ,
    }).buttons().container().appendTo("#datatable-buttons_wrapper .col-md-6:eq(0)"), $(".dataTables_length select").addClass("form-select form-select-sm")
});


// "copy","excel","pdf","colvis"