document.addEventListener("DOMContentLoaded", function () {
    let addAuthorBtn = document.getElementById("add-author");
    if (addAuthorBtn) {
        addAuthorBtn.addEventListener("click", function () {
            let newAuthorInput = document.getElementById("id_new_author");
            let authorDropdown = document.getElementById("id_author");

            let newAuthorName = newAuthorInput.value.trim();
            if (newAuthorName) {
                let newOption = new Option(newAuthorName, newAuthorName, true, true);
                authorDropdown.add(newOption);
                newAuthorInput.value = "";  // Clear input after adding
            }
        });
    }

    // Initialize Select2 for better search functionality
    $(document).ready(function () {
        $(".select2").select2();
    });
});
