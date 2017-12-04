.PHONY: upload submit user

TERRAFORM_PATH=~/_ega/terraform
GPG_EXEC=gpg
SSH_KEY_PUB=~/.ssh/lega.pub
SSH_KEY_PRIV=~/.ssh/lega

CEGA_IP=$(shell cd ${TERRAFORM_PATH}/cega && terraform output address)
INBOX_IP=$(shell cd ${TERRAFORM_PATH} && terraform output -module=inbox address)

define ORG_FILE
My present situation was one in which all voluntary thought was swallowed up and lost. I was hurried away by fury; revenge alone endowed me with strength and composure; it moulded my feelings and allowed me to be calculating and calm at periods when otherwise delirium or death would have been my portion.

My first resolution was to quit Geneva forever; my country, which, when I was happy and beloved, was dear to me, now, in my adversity, became hateful. I provided myself with a sum of money, together with a few jewels which had belonged to my mother, and departed.

And now my wanderings began which are to cease but with life. I have traversed a vast portion of the earth and have endured all the hardships which travellers in deserts and barbarous countries are wont to meet. How I have lived I hardly know; many times have I stretched my failing limbs upon the sandy plain and prayed for death. But revenge kept me alive; I dared not die and leave my adversary in being.

Tired of reading? Add this page to your Bookmarks or Favorites and finish it later.

When I quitted Geneva my first labour was to gain some clue by which I might trace the steps of my fiendish enemy. But my plan was unsettled, and I wandered many hours round the confines of the town, uncertain what path I should pursue. As night approached I found myself at the entrance of the cemetery where William, Elizabeth, and my father reposed. I entered it and approached the tomb which marked their graves. Everything was silent except the leaves of the trees, which were gently agitated by the wind; the night was nearly dark, and the scene would have been solemn and affecting even to an uninterested observer. The spirits of the departed seemed to flit around and to cast a shadow, which was felt but not seen, around the head of the mourner.

The deep grief which this scene had at first excited quickly gave way to rage and despair. They were dead, and I lived; their murderer also lived, and to destroy him I must drag out my weary existence. I knelt on the grass and kissed the earth and with quivering lips exclaimed, "By the sacred earth on which I kneel, by the shades that wander near me, by the deep and eternal grief that I feel, I swear; and by thee, O Night, and the spirits that preside over thee, to pursue the daemon who caused this misery, until he or I shall perish in mortal conflict. For this purpose I will preserve my life; to execute this dear revenge will I again behold the sun and tread the green herbage of earth, which otherwise should vanish from my eyes forever. And I call on you, spirits of the dead, and on you, wandering ministers of vengeance, to aid and conduct me in my work. Let the cursed and hellish monster drink deep of agony; let him feel the despair that now torments me."

I had begun my adjuration with solemnity and an awe which almost assured me that the shades of my murdered friends heard and approved my devotion, but the furies possessed me as I concluded, and rage choked my utterance.
endef


##############################

GPG_HOME=$(TERRAFORM_PATH)/private/gpg
GPG_EMAIL=$(shell awk -F= '/GPG_EMAIL/ {print $$2}' $(TERRAFORM_PATH)/bootstrap/settings.rc)
CEGA_MQ_CONNECTION=$(shell awk -F' ' '/CEGA_swe1_MQ_PASSWORD/ {print "amqp://cega_swe1:" $$3 "@localhost:5672/swe1"}' $(TERRAFORM_PATH)/cega/private/.trace)

##############################

all: user upload submit

export ORG_FILE
org:
	@echo "$${ORG_FILE}" > $@

enc: org
	$(GPG_EXEC) --homedir $(GPG_HOME) -r $(GPG_EMAIL) -e -o $@ $<

upload: user enc
	sftp -i $(SSH_KEY_PRIV) toto@${INBOX_IP} <<< $$'put enc'

enc.md5: enc
	md5 $< | cut -d' ' -f4 > $@

org.md5: org
	md5 $< | cut -d' ' -f4 > $@

submit: enc enc.md5 org.md5
	ssh -l centos ${CEGA_IP} /var/lib/cega/publish --connection $(CEGA_MQ_CONNECTION) swe1 toto enc --unenc $(shell cat org.md5) --enc $(shell cat enc.md5)

user: toto.yml
	scp $< centos@${CEGA_IP}:$<
	ssh -l centos ${CEGA_IP} "[[ -L /var/lib/cega/users/swe1/$< ]] || sudo ln -s ~/$< /var/lib/cega/users/swe1/$<"

toto.yml:
	@echo --- > $@
	@echo "pubkey: $(shell cat $(SSH_KEY_PUB))" >> $@

clean:
	rm -rf org enc enc.md5 org.md5 toto.yml
