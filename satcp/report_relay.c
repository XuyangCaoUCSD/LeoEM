#include <linux/netlink.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>
#include <errno.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <pthread.h>
#include <sys/time.h>
#include <stddef.h>

#define NETLINK_USER 31
#define UDP_SERVER_PORT 20001
#define MAX_PAYLOAD 1024 /* maximum payload size*/
#define SATCP_DURATION 2.3

struct sockaddr_nl src_addr, dest_addr;
struct nlmsghdr *nlh = NULL;
struct iovec iov;
int sock_fd;
struct msghdr msg;
int sockfd;
char buffer[MAX_PAYLOAD];
struct sockaddr_in servaddr, cliaddr;
int len, n;
pthread_mutex_t lock;
// most recent handover timestamp
struct timeval tv;
int current_handover_status; 

void * wait_and_send_handover_start_signal(void * no_arg) {

    while(1) {
        // receive updated handover status signal from the ground station
        n = recvfrom(sockfd, (char *)buffer, MAX_PAYLOAD, 
                MSG_WAITALL, ( struct sockaddr *) &cliaddr,
                &len);

        pthread_mutex_lock(&lock);
        printf("-------start handover 1-------\n");
        // update the handover timestamp
        current_handover_status = 1;
        gettimeofday(&tv, NULL);
        long double satcp_expiration_time = (tv.tv_sec + (long double) tv.tv_usec / 1000000) + SATCP_DURATION;
        printf("in start function: handover timestamp: %Lf\n", satcp_expiration_time);
        struct timeval current_tv;
        gettimeofday(&current_tv, NULL);
        long double current_time = (current_tv.tv_sec + (long double) current_tv.tv_usec / 1000000);
        printf("in start function: current timestamp: %Lf\n", current_time);
        buffer[n] = '\0';

        printf("received updated handover status signal: %s\n", buffer);
        strcpy(NLMSG_DATA(nlh), buffer);

        iov.iov_base = (void *)nlh;
        iov.iov_len = nlh->nlmsg_len;
        msg.msg_name = (void *)&dest_addr;
        msg.msg_namelen = sizeof(dest_addr);
        msg.msg_iov = &iov;
        msg.msg_iovlen = 1;
        // send the updated handover status to the kernel
        sendmsg(sock_fd, &msg, 0);
        printf("-------end handover 1-------\n");
        pthread_mutex_unlock(&lock);
    }
}

void * wait_and_send_handover_over_signal(void * no_arg) {
    while (1) {  
        pthread_mutex_lock(&lock);
        if (current_handover_status == 1) {
            long double satcp_expiration_time = (tv.tv_sec + (long double) tv.tv_usec / 1000000) + SATCP_DURATION;
            struct timeval current_tv;
            long double current_time = (current_tv.tv_sec + (long double) current_tv.tv_usec / 1000000);
            gettimeofday(&current_tv, NULL);
            if (satcp_expiration_time < current_time) {
                printf("-------start handover 0-------\n");
                printf("in over function: handover timestamp: %Lf\n", satcp_expiration_time);
                printf("in over function: current timestamp: %Lf\n", current_time);
                
                // send handover end signal
                char * signal = "0";
                printf("received updated handover status signal: %s\n", signal);
                strcpy(NLMSG_DATA(nlh), signal);
                iov.iov_base = (void *)nlh;
                iov.iov_len = nlh->nlmsg_len;
                msg.msg_name = (void *)&dest_addr;
                msg.msg_namelen = sizeof(dest_addr);
                msg.msg_iov = &iov;
                msg.msg_iovlen = 1;
                // send the updated handover status to the kernel
                sendmsg(sock_fd, &msg, 0);
                current_handover_status = 0;
                printf("-------end handover 0-------\n");
            }
        }
        pthread_mutex_unlock(&lock);
    }
}

int main()
{
    printf("SATCP duration is %f.\n", SATCP_DURATION);
    if (pthread_mutex_init(&lock, NULL) != 0) {
        printf("error when creating the mutex lock!\n");
        return 1;
    }
    gettimeofday(&tv, NULL);
    current_handover_status = 0;
    /* -----------------NETLINK SOCKET CREATION START-----------------*/
    sock_fd = socket(AF_NETLINK, SOCK_RAW, NETLINK_USER);
    // if (sock_fd < 0) {
    //     printf("error creating sock_fd: %d\n", sock_fd);
    //     printf("errno is %s\n", strerror(errno));
    //     return -1;
    // }

    // populate my own address
    memset(&src_addr, 0, sizeof(src_addr));
    src_addr.nl_family = AF_NETLINK;
    src_addr.nl_pid = getpid(); /* self pid */

    bind(sock_fd, (struct sockaddr *)&src_addr, sizeof(src_addr));

    // populate the kernel address
    memset(&dest_addr, 0, sizeof(dest_addr));
    dest_addr.nl_family = AF_NETLINK;
    dest_addr.nl_pid = 0; /* For Linux Kernel */
    dest_addr.nl_groups = 0; /* unicast */

    nlh = (struct nlmsghdr *)malloc(NLMSG_SPACE(MAX_PAYLOAD));
    memset(nlh, 0, NLMSG_SPACE(MAX_PAYLOAD));
    nlh->nlmsg_len = NLMSG_SPACE(MAX_PAYLOAD);
    nlh->nlmsg_pid = getpid();
    nlh->nlmsg_flags = 0;
    /* -----------------NETLINK SOCKET CREATION END-----------------*/

    /* -----------------UDP SOCKET CREATION START-----------------*/
    // creating socket file descriptor
    if ( (sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0 ) {
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }

    memset(&servaddr, 0, sizeof(servaddr));
    memset(&cliaddr, 0, sizeof(cliaddr));

    servaddr.sin_family = AF_INET; // IPv4
    servaddr.sin_addr.s_addr = INADDR_ANY;
    servaddr.sin_port = htons(UDP_SERVER_PORT);

    // bind the socket with the server address
    if ( bind(sockfd, (const struct sockaddr *)&servaddr, 
            sizeof(servaddr)) < 0 )
    {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }

    len = sizeof(cliaddr);
    /* -----------------UDP SOCKET CREATION START END-----------------*/
    pthread_t handover_start_report_thread;
    pthread_create(&handover_start_report_thread, NULL, wait_and_send_handover_start_signal, NULL);
    pthread_t handover_end_report_thread;
    pthread_create(&handover_end_report_thread, NULL, wait_and_send_handover_over_signal, NULL);
    pthread_join(handover_start_report_thread, NULL);


    close(sock_fd);
}
