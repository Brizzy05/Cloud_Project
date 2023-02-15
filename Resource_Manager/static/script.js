//Update the progress
const pod_url = "/cloud/dashboard/cluster/01"

function update_progress()
{
    var num_cluster_text = document.getElementById("cluster_num").innerHTML;
    var num_cluster_progress = document.getElementById("cluster_bar")

    var num_pod_text = parseInt(document.getElementById("pod_num").innerHTML);
    var num_pod_progress = document.getElementById("pod_bar")

    var num_node_text1 = parseInt(document.getElementById("node_num1").innerHTML);
    var num_node_text2 = parseInt(document.getElementById("node_num2").innerHTML);
    var num_node_progress = document.getElementById("node_bar")

    if (parseInt(num_cluster_text) == 0)
    {
        num_cluster_progress.style.width = "0"
    }

    if (num_pod_text == 0){
        num_pod_progress.style.width = "0"
    }

    if (num_node_text1 == 0 & num_node_text2 == 0){
        num_node_progress.style.width = "0"
    }
    else if (num_node_text1 == 0){
        num_node_progress.style.width = "100%"
    }
    else {
        perc = num_node_text1 / num_node_text2 * 100
        num_node_progress.style.width = perc + "%"
    }

}

function update_status(){
    var status_elm = document.getElementById("init");
    status_text = status_elm.innerHTML

    nav_link1 = document.getElementById("nav-link1");
    nav_link2 = document.getElementById("nav-link2");

    if (status_text !== 'Connected'){
        nav_link1.href = "#";
        nav_link2.href = "#";
        status_elm.style.backgroundColor = 'red';

    }

}

update_status()
update_progress()

