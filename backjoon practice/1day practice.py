# a= int(input())
# x = int 
# for i in range(a):
#     A,B=map(int,input().split())
#     x = 1 + i 
#     print('Case','#'+str(x) +':',A,'+',B,'=',str(A+B))
# =======================================================
# a = int(input())
# star = 0
# for i in range(1,a+1):
#     star = a -1
#     print(" "*(a-i) + "*"*i)
# ========================================================
# a,b = map(int,input().splite())
# c = list(map(int, input().split()))

# for i in range(a):
#     if c[i] >= b:
#         del c[i]

# print(c)
#=====================================================
# n,x = map(int,input().split())
# l = list(map(int,input().split()))
# a=[]
# for i in range(n):
#     if l[i]<x:
#         a.append(str(l[i]))
# print(" ".join(a))
# ====================================================
# while True:
#     a,b = map(int,input().split());
#     if a==0 and b==0:
#         break
#     else :
#         print(a+b)
# while True:
#     try:
#         a,b =map(int,input().split())
#         print(a+b)
#     except:
#         break
# # ==========================================
# 26부터 시작한다. 2+6 = 8이다. 새로운 수는 68이다.
# 위의 예는 4번만에 원래 수로 돌아올 수 있다. 따라서 26의 사이클의 길이는 4이다. 사이클이 도는 프로그램을 작성해라
# n=int(input())
# cnt=0
# a = n
# while True:
#     sum_num=(a//10)+(a%10)
#     new_num=((a%10)*10)+(sum_num%10)
#     cnt+=1
#     if new_num==n:
#         print(cnt)
#         break
#     a=new_num
# ============================================
h,m = map(int,input().split())
c = int(input())

a = c//60
b = c%60

h+=a
m+=b

if m>=60:
    m-=60
    h+=1

if h>23:
    h-=24
    
print(h,m)